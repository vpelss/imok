#!/usr/bin/perl -d

use strict;
use Socket;
use lib '.'; #nuts, PERL has changed. add local path to @INC
use lib './'; #nuts, PERL has changed. add local path to @INC
#use lib '/home/cgi/imok/'; #nuts, PERL has changed. add local path to @INC
#use lib '/home/emogic/public_html/cgi/imok/'; #nuts, PERL has changed. add local path to @INC
use AuthorizeMe;

my %in;

my $path_to_templates = './templates';
my $logged_in;
my $trigger_time = 0;

#test no obj
$AuthorizeMe::email = "hhhhhhhhh";
AuthorizeMe::test;

#initialize and create AutorizeMe
my $user; # a hash ref as we want to be able to easily get hash from AuthorizeMe
#db structure for AutorizeMe : we can easily add db fields here, but username email and password are a MUST for the AuthorizeMe.pm
=pod
$user{'name'} = ''; #meant to be first and last name
$user{'user_id'} = '';
$user{'email'} = '';
$user{'password'} = '';
$user{'email_contact_1'} = '';
$user{'email_contct_2'} = '';
$user{'email_contact_3'} = '';
$user{'email_form'} = '';
$user{'time_out'} = '86400'; #24 hours
$user{'start_hour'} = '12';
$user{'start_minute'} = '00';
$user{'alerts_sent'} = 0;
=cut

my %AuthorizeMe_Settings;
$AuthorizeMe_Settings{'token_name'} = 'imok_token'; #will show up in cookie
$AuthorizeMe_Settings{'token_max-age'} = '3153600000'; #string time in seconds the cookie will live
$AuthorizeMe_Settings{'user_id_name'} = 'imok_user_id'; #will show up in cookie
$AuthorizeMe_Settings{'from_email'} = 'imok@emogic.com';
$AuthorizeMe_Settings{'reply_email'} = 'imok@emogic.com';
$AuthorizeMe_Settings{'sendmail'} = '/usr/lib/sendmail -t';
$AuthorizeMe_Settings{'smtp_server'} = '';
$AuthorizeMe_Settings{'Activation_Email_Subject'} = 'IMOK account activation email';
$AuthorizeMe_Settings{'registration_email_template'} = qq(You have registered for an IMOK account.
    Click to activate:
    https://www.emogic.com/cgi/imok/imok.cgi?command=activate&activate_code=<%activate_code%>&user_id=<%user_id%>
    );
 $AuthorizeMe_Settings{'forgot_password_email_template'} = qq(You have requested a password recovery for an IMOK account.
    Click the link to reset your password to <%set_password_code%>:
    http://localhost/cgi/imok/imok.cgi?command=set_password&user_id=<%user_id%>&set_password_code=<%set_password_code%>
    );
$AuthorizeMe_Settings{'path_to_users'} = './users/';
$AuthorizeMe_Settings{'path_to_tokens'} = './tokens/';
$AuthorizeMe_Settings{'path_to_authorizations'} = './authorizations/';

#$AuthorizeMe::user = \%user; #no object option? Can the variables be set?
#$AuthorizeMe::AuthorizeMe_Settings = \%AuthorizeMe_Settings; #no object option? Can the variables be set?
#$logged_in = &AuthorizeMe::AmILoggedIn();

#my $AuthorizeMeObj = AuthorizeMe->new( \%user , \%AuthorizeMe_Settings ); #pass %user by reference when we create this object so we can update it in main, module can take value, update it, save, and return it to main
my $AuthorizeMeObj = AuthorizeMe->new( \%AuthorizeMe_Settings );

my $last_message = '';

eval { &main(); };     # Trap any fatal errors so the program hopefully
if ($@) { &cgierr("fatal error: $@"); }     # never produces that nasty 500 server error page.
exit;   # There are only two exit calls in the script, here and in in &cgierr.

sub main(){
if ( $ARGV[0] eq 'cron' ) { &cron(); exit;} #from cron so exit.
#&cron();
%in = &parse_form();
my $command = $in{'command'};

my $output = '';
$output = &get_template_page('main.html');

#$logged_in = &AuthorizeMe::AmILoggedIn();
$user = $AuthorizeMeObj->AmILoggedIn();

if ( defined($user) ) {#we are logged in
#if($logged_in == 1) {#we are logged in
    if ( $command eq 'logout' ) { &logout() } #login email , password
    if ( $command eq 'logout_all_devices' ) { &logout_all_devices() }
    if ( $command eq 'reset_password' ) { &reset_password($in{'current_password'} , $in{'new_password'}) }
    if ( $command eq 'get_settings' ) { &get_settings(\$output) }
    if ( $command eq 'set_settings' ) { &set_settings() }
    if ( $command eq 'imok' ) { &imok() }
    if ( $command eq 'imnotok' ) { &imnotok() }
    }
else{#we are not logged in
    if ( $command eq 'register' ) { &register(); } #load register form from ./forms/register.html or just jump to it?
				if ( $command eq 'activate' ) { &activate($in{'activate_code'} , $in{'user_id'}) } #login email , password
    if ( $command eq 'login' ) { &login() } #login email , password
    if ( $command eq 'forgot_password' ) { &forgot_password($in{'email'}) }
    if ( $command eq 'set_password' ) { &set_password($in{'user_id'} , $in{'set_password_code'}); }#from link sent by &forgot_password
    }

if ( $command eq 'cron' ) { &cron() } #so we can trigger it web

$logged_in = $AuthorizeMeObj->AmILoggedIn();
if($logged_in == 1) {#we are logged in
    $output =~ s/<%logged_out%>/hide_me/g; #hide login, register , forgot pw
    $output =~  s/<%logged_in%>/show_me/g; #show logout, settings, reset pw
    if($trigger_time != 0) {$output =~  s/<%trigger_time%>/$trigger_time/g;} #for main page  != 0
    }
else{
    $output =~ s/<%logged_out%>/show_me/g; #show login, register , forgot pw
    $output =~  s/<%logged_in%>/hide_me/g; #hide logout, settings, reset pw
    }

$output =~  s/<%last_message%>/$last_message/g;
my $set_cookie_string = $AuthorizeMeObj->get_set_cookie_string();
print "Content-type: text/html\n";
print "Cache-Control: max-age=0\n";
print "Cache-Control: no-store\n";
print "$set_cookie_string\n\n";
print $output;
} #main done

sub write_to_log(){
 my $text = shift;
 my $filename = 'log.txt';
 my $MAXSIZE = 2**15;

 if(-s $filename > $MAXSIZE){
  open(FH, '<', $filename);
  my @lines = <FH>;
  close FH;
  my $number_of_lines = scalar @lines;
  for(my $i = 0 ; $i < ($number_of_lines/2) ; $i++){
   shift @lines;
  }
  open(FH, '>', $filename) or return 0;
  print FH @lines;
  close FH;
 }

 open(FH, '>>', $filename) or return 0;# $!;
 print FH "$text\n\n";
 close(FH);
 return 1;
}

sub imok(){
my $user = $AuthorizeMeObj->AmILoggedIn(); #get user details
if( !defined($user) ){return 0;}
my $filename = "$AuthorizeMe_Settings{'path_to_users'}/$user->{'user_id'}";
my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$current_time_stamp,$ctime,$blksize,$blocks) = stat($filename);
my $new_time_stamp = $current_time_stamp; #will ALWAYS jump to next start_time (after now) + time_out
my $now = time();

if( $current_time_stamp <= $now ){#alarm was/is triggered
  until( $new_time_stamp  > $now ){
   $new_time_stamp = $new_time_stamp + $user->{'timeout_ms'};
  }
 #$new_time_stamp = $new_time_stamp + $user{'timeout_ms'};
 $last_message = "$last_message Alarm was likely triggered. Please email your contacts and tell them you are OK.";
 #send out IMOK email. Member has checked in...
}
elsif( ($current_time_stamp - $user->{'timeout_ms'}) <= $now ){ #we are clicking just before alarm is triggered
 $new_time_stamp = $current_time_stamp + $user->{'timeout_ms'};
}
elsif( ($current_time_stamp - $user->{'timeout_ms'}) > $now  ){# we are a full timeout before the time stamp. do nothing
 #do nothing
}
elsif( ($current_time_stamp - (2 * $user->{'timeout_ms'}) ) > $now ){#time stamp is greater than 2 or more full timeouts, this should never happen, but if it does, imok moves us
 #do nothing
}

#trigger time on users comp?
my $new_time_stamp_user_tz = $new_time_stamp + ($user->{'tz_offset_hours' } * 60 * 60);
my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = gmtime($new_time_stamp_user_tz);
$mon = $mon + 1;
$year = 1900 + $year;
my $trigger_time_string = sprintf("%d-%.2d-%.2d  %d:%.2d", $year , $mon , $mday , $hour , $min);


my $result = &change_time_stamp($new_time_stamp , $filename);
if($result == 1){
 $last_message = "$last_message your next IMOK trigger time is: $trigger_time_string";
}
else{
 $last_message = "$last_message IMOK trigger time failed. Please try again.";
}
 &write_to_log("$user->{'email'} checked in.");
return $result;
}

sub imnotok(){
 my $result = &AuthorizeMe::sendmail($AuthorizeMe_Settings{'from_email'} , $AuthorizeMe_Settings{'reply_email'} , $user->{'email_contact_1'} , $AuthorizeMe_Settings{'sendmail'} , 'IMOK Alert' , $user->{'email_form'} , '');
 &write_to_log("sendmail result : $result : $user->{'email_contact_1'} : $user->{'email'}");
 $last_message = "sendmail result : $result : $user->{'email_contact_1'} : $user->{'email'}";
}

sub cron(){
 #get list of files in a directory
  &write_to_log("start of cron");
 my @filenames = glob("$AuthorizeMe_Settings{'path_to_users'}*");
 foreach my $filename (@filenames){
  #$filename = "$AuthorizeMe_Settings{'path_to_users'}$filename";
  my $timestamp = &get_time_stamp($filename);
  if($timestamp > time()){#we are not alarming
   next;
  }
  $user = &AuthorizeMe::db_to_hash($filename); #open file get details
 # &write_to_log("Result of user db $result user $user->{'user_id'}");
  #send alert emails
  #($from, $reply, $to, $smtp, $subject, $message ,$SMTP_SERVER)
  my $result = &AuthorizeMe::sendmail($AuthorizeMe_Settings{'from_email'} , $AuthorizeMe_Settings{'reply_email'} , $user->{'email_contact_1'} , $AuthorizeMe_Settings{'sendmail'} , 'IMOK Alert' , $user->{'email_form'} , '');
   &write_to_log("sendmail result : $result : $user->{'email_contact_1'} : $user->{'email'}");
 $result = &AuthorizeMe::sendmail($AuthorizeMe_Settings{'from_email'} , $AuthorizeMe_Settings{'reply_email'} , $user->{'email_contact_2'} , $AuthorizeMe_Settings{'sendmail'} , 'IMOK Alert' , $user->{'email_form'} , '');
  $result = &AuthorizeMe::sendmail($AuthorizeMe_Settings{'from_email'} , $AuthorizeMe_Settings{'reply_email'} , $user->{'email_contact_3'} , $AuthorizeMe_Settings{'sendmail'} , 'IMOK Alert' , $user->{'email_form'} , '');
  #&write_to_log("sendmail result : $result : $user{'email_contact_1'} : $user{'email'}");
  #set time stamp ahead one hour. So we do not send an email for another hour
  $user->{'timestamp'} = (60 * 60) + $timestamp;
  #increase email file count
  $user->{'alerts_sent'} = 1 + $user->{'alerts_sent'};
  #save file
  &AuthorizeMe::hash_to_db($user , $filename);
  #&AuthorizeMe::user_to_db(\%user , $filename);
  #update time stamp
  &change_time_stamp($user->{'timestamp'} , $filename);
  &write_to_log("$filename Alert to $user->{'user_id'} $user->{'email_contact_1'} $user->{'email_contact_1'} at $user->{'timestamp'}");
  $last_message = "$last_message email alert sent $user->{'timestamp'}";
 }

}

sub change_time_stamp(){
 my $new_time_stamp = shift;
 my $filename = shift;
 my $result = utime($new_time_stamp , $new_time_stamp , $filename);
 return $result;
}

sub get_time_stamp(){
 my $filename = shift;
 open(FH, '<', $filename) or return 0;# $!;
 my $epoch_timestamp = (stat(FH))[9];
 close FH;
 return $epoch_timestamp;
}

sub time_zone(){
 my $hour_seconds = 60 * 60;
 my $day_seconds = 24 * $hour_seconds;
 #what is today's time at 12:00
 my $right_now = time();
 my $days = $right_now / $day_seconds;
 my $years = $right_now / ($day_seconds * 365);
 my $days_rounded = sprintf("%d", $days);
 my $today_seconds_at_00 = $days_rounded  * $day_seconds;
 #calc time zone offset
 my @lt = localtime($today_seconds_at_00 + ($day_seconds/2)); #must use noon or we will get odd values
 my $tz = $lt[2] - 12; #calc timezome difference, includes DST
 return $tz;
}

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
 $$output = &get_template_page('settings.html'); #string passed by ref so we can modify it
 #get user data
 $user = $AuthorizeMeObj->AmILoggedIn();
 if(!defined($user)){return 0}
 #replace tokens
 $$output =~ s/<%email_contact_1%>/$user->{'email_contact_1'}/g; #hide login, register , forgot pw
 $$output =~ s/<%email_contact_2%>/$user->{'email_contact_2'}/g; #hide login, register , forgot pw
 $$output =~ s/<%email_contact_3%>/$user->{'email_contact_3'}/g; #hide login, register , forgot pw
 $$output =~  s/<%email_form%>/$user->{'email_form'}/g; #show logout, settings, reset pw
 $$output =~  s/<%time_out%>/$user->{'time_out'}/g; #show logout, settings, reset pw
 $$output =~  s/<%start_date%>/$user->{'start_date'}/g; #show logout, settings, reset pw
 $$output =~  s/<%start_time%>/$user->{'start_time'}/g; #show logout, settings, reset pw
}

sub set_settings(){
 $user = $AuthorizeMeObj->AmILoggedIn();
 if(!defined($user)){ return 0; }
 my $email = $in{'email_contact_1'};
 if(($email eq '') || (AuthorizeMe::valid_email($email))){
  $user->{'email_contact_1'} = $email;
 }
 else{
  $last_message = "$last_message : $email is not a valid email address";
  return 0;
 }
 $email = $in{'email_contact_2'};
 if(($email eq '') || (AuthorizeMe::valid_email($email))){
  $user->{'email_contact_2'} = $email;
 }
 else{
  $last_message = "$last_message : $email is not a valid email address";
  return 0;
 }
 $email = $in{'email_contact_3'};
 if(($email eq '') || (AuthorizeMe::valid_email($email))){
  $user->{'email_contact_3'} = $email;
 }
 else{
  $last_message = "$last_message : $email is not a valid email address";
  return 0;
 }

 $user->{'email_form'} = $in{'email_form'};
 $user->{'time_out'} = $in{'time_out'};
 $user->{'timeout_ms'} = 24 * 60 * 60 * $in{'time_out'};

 $user->{'start_date'} = $in{'start_date'};
 $user->{'start_time'} = $in{'start_time'};

 $user->{'tz_offset_hours'} = $in{'tz_offset_hours'};
 $user->{'timestamp'} = $in{'timestamp'};

 #my $result = $AuthorizeMeObj->hash_to_db(\%user , );
 #get_user_id
 my $user_id = $AuthorizeMeObj->get_user_id();
 my $result = $AuthorizeMeObj->user_to_db($user_id);
 #$result = imok();
 if($result == 1){
  $last_message = "$last_message Settings changed.";
  }
 else{
  $last_message = "$last_message Settings not changed.";
  }

 my $hour_seconds = 60 * 60;
 my $day_seconds = 24 * $hour_seconds;
 my $timestamp = $user->{'timestamp'}; #trigger timestamp based on PC's local time
 $result = &change_time_stamp($timestamp , "$AuthorizeMe_Settings{'path_to_users'}$user->{'user_id'}");
 if($result == 0){
  $last_message = "$last_message Could not set timestamp on $AuthorizeMe_Settings{'path_to_users'}$user->{'user_id'}";
  }
 my @lt = localtime($timestamp);
 my $str_time = sprintf("%d:%.2d", $lt[2] , $lt[1]);
 my $year = 1900 + $lt[5];
 my $month = $lt[4] + 1;
 $last_message = "$last_message Trigger time is $year-$month-$lt[3] $str_time on the server and $in{'start_date'} $in{'start_time'} local time on your pc";
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
 my $user_id = shift;

 $user =  $AuthorizeMeObj->activate( $authorize_code , $user_id );
 if(!defined($user)) {$last_message = "$last_message Your activation failed."; return 0};
 $user->{'email_contact_1'} = '';
 $user->{'email_contct_2'} = '';
 $user->{'email_contact_3'} = '';
 $user->{'email_form'} = 'Member has not reported in to IMOK in a specified amount of time. You may want to check on them.';
 $user->{'timeout_ms'} = '86400000'; #24hours
 my $filename = "$AuthorizeMe_Settings{'path_to_users'}$user->{'user_id'}";

# my $result =  $AuthorizeMeObj->user_to_db();
 my $result =  $AuthorizeMeObj->hash_to_db(\$user , $filename);
 
 if($result == 0) {$last_message = "$last_message Your activation failed. DB write error."; return 0};

 #$result = imok();
 if($result == 1){
  $last_message = "$last_message Your account $user->{'email'} has been authorized. Please log in and go to setup.";
  }
 else{
  $last_message = "$last_message Error: Your account $user->{'email'} could not be authorized";
  }
 return $result;
 }

sub login(){
 #email points to data file
 my $result =  $AuthorizeMeObj->login( $in{'email'} , $in{'password'} );
 if($result == 1){
  $last_message = "$last_message $user->{'email'} has logged in";
  }
 else{
  $last_message = "$last_message $user->{'email'} could not log in";
  }
 return $result;
}

sub logout(){
 my $result =  $AuthorizeMeObj->logout();
 if($result == 1){
  $last_message = "$last_message $user->{'email'} has logged out";
  }
 else{
  $last_message = "$last_message $user->{'email'} could not log out";
  }
 }

sub logout_all_devices(){
 my $result =  $AuthorizeMeObj->logout_all_devices();
 if($result == 1){
  $last_message = "$last_message $user->{'email'} has logged out of all devices";
  }
 else{
  $last_message = "$last_message $user->{'email'} could not log out of all devices";
  }
}

sub forgot_password(){
 my $email = shift;
 my $result = $AuthorizeMeObj->forgot_password($email);
 if($result == 1){
  $last_message = $AuthorizeMeObj->get_last_message();;
  }
 else{
  $last_message = "$last_message $email could not recover password";
  }
 return $result;
}

sub set_password(){
 my $user_id = shift;
 my $set_password_code = shift;
 my $result = $AuthorizeMeObj->set_password($user_id,$set_password_code);
 if($result == 1){
  $last_message = "$last_message Password was reset";
  }
 else{
  $last_message = "$last_message Password was not reset";
  }
 return $result;
}

sub reset_password(){
 my $current_password = shift;
 my $new_password = shift;
 my $result = $AuthorizeMeObj->reset_password($current_password,$new_password);
 if($result == 1){
  $last_message = "$last_message Password was reset";
  }
 else{
  $last_message = "$last_message Password was not reset";
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

#if (my $debug == 0) {
 #    print "Epic fail....";
  #   }
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
