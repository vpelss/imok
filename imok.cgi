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
$user{'timeout_ms'} = '';
my %AuthorizeMe_Setup;
$AuthorizeMe_Setup{'domain'} = 'localhost'; #will show up in cookie
$AuthorizeMe_Setup{'Token_Name'} = 'imok_token'; #will show up in cookie
$AuthorizeMe_Setup{'User_ID_Name'} = 'imok_user_id'; #will show up in cookie
#$AuthorizeMe_Setup{'Token_Max-Age'} = '3153600000'; #string time in seconds the cookie will live
$AuthorizeMe_Setup{'From_Email'} = 'imok@emogic.com'; 
$AuthorizeMe_Setup{'Reply_Email'} = 'imok@emogic.com'; 
$AuthorizeMe_Setup{'SEND_MAIL'} = '/usr/lib/sendmail -t';
$AuthorizeMe_Setup{'SMTP_SERVER'} = '';
$AuthorizeMe_Setup{'path_to_users'} = './users/'; 
$AuthorizeMe_Setup{'path_to_users'} = './users/'; 
$AuthorizeMe_Setup{'path_to_tokens'} = './tokens/'; 
$AuthorizeMe_Setup{'user_file_extension'} = ''; 
my $AuthorizeMeObj = AuthorizeMe->new( \%user , \%AuthorizeMe_Setup ); #pass %user by reference when we create this object so we can update it in main, module can take value, update it, save, and return it to main

my $last_message = '';

eval { &main(); };     # Trap any fatal errors so the program hopefully
if ($@) { &cgierr("fatal error: $@"); }     # never produces that nasty 500 server error page.
exit;   # There are only two exit calls in the script, here and in in &cgierr.

sub main(){
#$logged_in = $AuthorizeMeObj->AmILoggedIn(); #moment of truth. was determined in new()

%in = &parse_form();
my $command = $in{'command'};

my $output = '';
$output = &get_template_page('main.html');
 
#if($logged_in == 1) {#we are logged in
    if ( $command eq 'logout' ) { &logout() } #login email , password
    #if ( $command eq 'reset_password' ) { &reset_password(); } 
#    }
#else{#we are not logged in
    if ( $command eq 'register' ) { &register(); } #load register form from ./forms/register.html or just jump to it?
				if ( $command eq 'activate' ) { &activate($in{'activate_code'}) } #login email , password		
    if ( $command eq 'login' ) { &login() } #login email , password
    #if ( $command eq 'forgot_password' ) { &forgot_password(); } #resend_password email
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

sub reset_password()
    { #get data
 
     }

sub forgot_password()
     { #get data

     }

sub replace_tokens_with{
	#$_[0] : token <%token%>
	#$_[1] : "replace text string"
	#$_[2] : "HTML string"
};

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
