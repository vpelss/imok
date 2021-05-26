#!C:/Perl64/bin/perl.exe -w -d

#!/usr/bin/perl

# Lock files in use

use strict;
use Socket;
use AuthorizeMe;

my %in;

my $path_to_templates = './templates';
my $logged_in;

#initialize and create AutorizeMe
my %user; # db structure for AutorizeMe : we can easily add db fields here, but username email and password are a MUST for the AuthorizeMe.pm
$user{'name'} = ''; #meant to be first and last name
$user{'user_id'} = '';
$user{'email'} = '';
$user{'password'} = '';
$user{'email_contact_1'} = '';
$user{'email_contct_2'} = '';
$user{'email_contact_3'} = '';
$user{'email_form'} = '';
$user{'time_out'} = '';
my %AuthorizeMe_Settings;
$AuthorizeMe_Settings{'token_name'} = 'imok_token'; #will show up in cookie
$AuthorizeMe_Settings{'token_max-age'} = '3153600000'; #string time in seconds the cookie will live
$AuthorizeMe_Settings{'user_id_name'} = 'imok_user_id'; #will show up in cookie
$AuthorizeMe_Settings{'from_email'} = 'imok@emogic.com'; 
$AuthorizeMe_Settings{'reply_email'} = 'imok@emogic.com'; 
$AuthorizeMe_Settings{'sendmail'} = '/usr/lib/sendmail -t';
$AuthorizeMe_Settings{'smtp_server'} = '';
$AuthorizeMe_Settings{'registration_email_template'} = qq(You have registered for an IMOK account.
    Click to activate:
    http://localhost/cgi/imok/imok.cgi?command=activate&activate_code=<%activate_code%>
    );
 $AuthorizeMe_Settings{'forgot_password_email_template'} = qq(You have requested a password recovery for an IMOK account.
    Click the link to reset your password to <%set_password_code%>:
    http://localhost/cgi/imok/imok.cgi?command=set_password&user_id=<%user_id%>&set_password_code=<%set_password_code%>
    );
$AuthorizeMe_Settings{'path_to_users'} = './users/'; 
$AuthorizeMe_Settings{'path_to_tokens'} = './tokens/'; 
$AuthorizeMe_Settings{'path_to_authorizations'} = './authorizations/'; 
my $AuthorizeMeObj = AuthorizeMe->new( \%user , \%AuthorizeMe_Settings ); #pass %user by reference when we create this object so we can update it in main, module can take value, update it, save, and return it to main

my $last_message = '';

eval { &main(); };     # Trap any fatal errors so the program hopefully
if ($@) { &cgierr("fatal error: $@"); }     # never produces that nasty 500 server error page.
exit;   # There are only two exit calls in the script, here and in in &cgierr.

sub main(){
%in = &parse_form();
my $command = $in{'command'};

my $output = '';
$output = &get_template_page('main.html');

$logged_in = $AuthorizeMeObj->AmILoggedIn(); 

#if($logged_in == 1) {#we are logged in
    if ( $command eq 'logout' ) { &logout() } #login email , password
    if ( $command eq 'logout_all_devices' ) { &logout_all_devices() } 
    if ( $command eq 'reset_password' ) { &reset_password($in{'current_password'} , $in{'new_password'}) } 
    if ( $command eq 'get_settings' ) { &get_settings(\$output) } 
    if ( $command eq 'set_settings' ) { &set_settings() } 
#    }
#else{#we are not logged in
    if ( $command eq 'register' ) { &register(); } #load register form from ./forms/register.html or just jump to it?
				if ( $command eq 'activate' ) { &activate($in{'activate_code'}) } #login email , password		
    if ( $command eq 'login' ) { &login() } #login email , password
    if ( $command eq 'forgot_password' ) { &forgot_password($in{'email'}) } 
    if ( $command eq 'set_password' ) { &set_password($in{'user_id'} , $in{'set_password_code'}); }#from link sent by &forgot_password
#    }

$logged_in = $AuthorizeMeObj->AmILoggedIn();
if($logged_in == 1) {#we are logged in
    $output =~ s/<%logged_out%>/hide_me/g; #hide login, register , forgot pw
    $output =~  s/<%logged_in%>/show_me/g; #show logout, settings, reset pw 
 }
else{
    $output =~ s/<%logged_out%>/show_me/g; #show login, register , forgot pw
    $output =~  s/<%logged_in%>/hide_me/g; #hide logout, settings, reset pw 
}
 
$output =~  s/<%last_message%>/$last_message/g;
my $set_cookie_string = $AuthorizeMeObj->get_set_cookie_string();
print "Content-type: text/html\n";
print "$set_cookie_string\n\n";
print $output;
} #main done

sub get_template_page(){
  #shift;
  my $filename = shift;
  my $output = '';
  open(FH, '<', "$path_to_templates/$filename") or die $!;
  while(<FH>){
   $output = $output . $_;
  }
  close FH;
  return $output;
}

sub get_settings(){
 my $output = shift; #string passed by ref so we can modify it
 $$output = &get_template_page('settings.html');
 #get user data
 $logged_in = $AuthorizeMeObj->AmILoggedIn();
 if($logged_in == 0){return 0}
 #replace tokens
 $$output =~ s/<%email_contact_1%>/$user{'$email_contact_1'}/g; #hide login, register , forgot pw
 $$output =~ s/<%email_contact_2%>/$user{'$email_contact_2'}/g; #hide login, register , forgot pw
 $$output =~ s/<%email_contact_3%>/$user{'$email_contact_3'}/g; #hide login, register , forgot pw
 $$output =~  s/<%email_form%>/$user{'email_form'}/g; #show logout, settings, reset pw  
 $$output =~  s/<%time_out%>/$user{'time_out'}/g; #show logout, settings, reset pw  
}

sub set_settings(){
 $logged_in = $AuthorizeMeObj->AmILoggedIn();
 $user{'email_contact_1'} = $in{'email_contact_1'};
 $user{'email_contct_2'} = $in{'email_contact_2'};
 $user{'email_contact_3'} = $in{'email_contact_3'};
 $user{'email_form'} = $in{'email_form'};
 $user{'time_out'} = $in{'time_out'};
 my $result = $AuthorizeMeObj->user_to_db();
 if($result == 1){
  $last_message = 'Settings changed';
  }
 else{
  $last_message = "Settings not changed";
  }
 return $result;
}

sub send_output
{
my $message = $_[0];
#print "Status: 401\n";
#print "WWW-Authenticate: Basic\n";
print "Content-type: text/html\n\n";
print $message;
exit;
}

sub register() { 
	my $email = $in{'email'};
	my $password = $in{'password'}; 
	my $result = $AuthorizeMeObj->register_account($email , $password);

 $last_message = $AuthorizeMeObj->get_last_message();
 return $result;
 }

sub activate(){
 my $authorize_code = shift;
 my $result =  $AuthorizeMeObj->activate( $authorize_code );
 if($result == 1){
  $last_message = "Your account $user{'email'} has been authorized";
  }
 else{
  $last_message = "Error: Your account $user{'email'} could not be authorized";
  }
 return $result;
 }

sub login(){
 #email points to data file
 my $result =  $AuthorizeMeObj->login( $in{'email'} , $in{'password'} );
 if($result == 1){
  $last_message = "$user{'email'} has logged in";
  }
 else{
  $last_message = "$user{'email'} could not log in";
  }
 return $result;
}

sub logout(){
 my $result =  $AuthorizeMeObj->logout();
 if($result == 1){
  $last_message = "$user{'email'} has logged out";
  }
 else{
  $last_message = "$user{'email'} could not log out";
  }
 }

sub logout_all_devices(){
 my $result =  $AuthorizeMeObj->logout_all_devices();
 if($result == 1){
  $last_message = "$user{'email'} has logged out of all devices";
  }
 else{
  $last_message = "$user{'email'} could not log out of all devices";
  }
}

sub forgot_password(){
 my $email = shift;
 my $result = $AuthorizeMeObj->forgot_password($email);
 if($result == 1){
  $last_message = $AuthorizeMeObj->get_last_message();;
  }
 else{
  $last_message = "$email could not recover password";
  }
 return $result;
}

sub set_password(){
 my $user_id = shift;
 my $set_password_code = shift;
 my $result = $AuthorizeMeObj->set_password($user_id,$set_password_code);
 if($result == 1){
  $last_message = "Password was reset";
  }
 else{
  $last_message = "Password was not reset";
  }
 return $result; 
}

sub reset_password(){
 my $current_password = shift;
 my $new_password = shift;
 my $result = $AuthorizeMeObj->reset_password($current_password,$new_password);
 if($result == 1){
  $last_message = "Password was reset";
  }
 else{
  $last_message = "Password was not reset";
  }
 return $result; 
 }

sub parse_form
{
# --------------------------------------------------------
# Parses the form input and returns a hash with all the name
# value pairs. Removes SSI and any field with "---" as a value
# (as this denotes an empty SELECT field.

        my (@pairs, %in);
        my ($buffer, $pair, $name, $value);

        if ($ENV{'REQUEST_METHOD'} eq 'GET') {
                @pairs = split(/&/, $ENV{'QUERY_STRING'});
        }
        elsif ($ENV{'REQUEST_METHOD'} eq 'POST') {
                read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
                 @pairs = split(/&/, $buffer);
        }
        else {
                &cgierr ("This script must be called from the Web\nusing either GET or POST requests\n\n");
        }
        PAIR: foreach $pair (@pairs) {
                ($name, $value) = split(/=/, $pair);

                $name =~ tr/+/ /;
                $name =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

                $value =~ tr/+/ /;
                $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

                $value =~ s/<!--(.|\n)*-->//g;                          # Remove SSI.
                if ($value eq "---") { next PAIR; }                  # This is used as a default choice for select lists and is ignored.
                (exists $in{$name}) ?
                        ($in{$name} .= "~~$value") :              # If we have multiple select, then we tack on
                        ($in{$name}  = $value);                                  # using the ~~ as a seperator.
        }
        return %in;
}

sub cgierr
{
# --------------------------------------------------------
# Displays any errors and prints out FORM and ENVIRONMENT
# information. Useful for debugging.

if (my $debug == 0) {
     print "Epic fail....";
     }
print "Content-Type: text/html\n\n";
print "<PRE>\n\nCGI ERROR\n==========================================\n";
$_[0]      and print "Error Message       : $_[0]\n";
$0         and print "Script Location     : $0\n";
$]         and print "Perl Version        : $]\n";

    print "\nForm Variables\n-------------------------------------------\n";
    foreach my $key (sort keys %in)
            {
            my $space = " " x (20 - length($key));
            print "$key$space: $in{$key}\n";
            }

    print "\nEnvironment Variables\n-------------------------------------------\n";
    foreach my $env (sort keys %ENV)
            {
            my $space = " " x (20 - length($env));
            print "$env$space: $ENV{$env}\n";
            }
print "\n</PRE>";

exit -1;
};
