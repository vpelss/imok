#!/usr/bin/perl

use strict;
use Socket;
use lib '.'; #nuts, PERL has changed. add local path to @INC
use AuthorizeMe;

my %in;

my $path_to_templates = './';

#create and initialize AutorizeMe
my $AuthorizeMeObj = AuthorizeMe->new();
#set all settings
$AuthorizeMeObj->{'settings'}->{'token_name'} = 'imok_token'; #will show up in cookie
$AuthorizeMeObj->{'settings'}->{'token_max-age'} = '3153600000'; #string time in seconds the cookie will live
$AuthorizeMeObj->{'settings'}->{'user_id_name'} = 'imok_user_id'; #will show up in cookie

$AuthorizeMeObj->{'settings'}->{'email_sendmail'} = '/usr/lib/sendmail -t';
$AuthorizeMeObj->{'settings'}->{'email_smtp_server'} = ''; #mail.emogic.com
$AuthorizeMeObj->{'settings'}->{'email_smtp_port'} = '25'; #26
$AuthorizeMeObj->{'settings'}->{'email_smtp_helo'} = 'emogic.com';
$AuthorizeMeObj->{'settings'}->{'email_from'} = 'imok@emogic.com';
$AuthorizeMeObj->{'settings'}->{'email_reply'} = 'imok@emogic.com';
#later
$AuthorizeMeObj->{'settings'}->{'email_to'} = '';#provide later
$AuthorizeMeObj->{'settings'}->{'email_subject'} = '';#provide later
$AuthorizeMeObj->{'settings'}->{'email_message'} = '';#provide later
#to send, set above, then $AuthorizeMeObj->email();

$AuthorizeMeObj->{'settings'}->{'forgot_password_email_subject'} = 'Password Reset - IMOK';
$AuthorizeMeObj->{'settings'}->{'Activation_Email_Subject'} = 'IMOK account activation email';
$AuthorizeMeObj->{'settings'}->{'registration_email_template'} = qq(You have registered for an IMOK account.

    Click this link to activate your account:
    <a target='_blank' href="https://www.emogic.com/cgi/imok/imok.cgi?command=activate&activate_code=<%activate_code%>&user_id=<%user_id%>">https://www.emogic.com/cgi/imok.cgi/imok?command=activate&activate_code=<%activate_code%>&user_id=<%user_id%></a>

    Then login, and enter the required settings for your account.
    );
$AuthorizeMeObj->{'settings'}->{'forgot_password_email_template'} = qq(You have requested a password recovery for an IMOK account.
    Click the link to reset your password to <%set_password_code%>:
    https://www.emogic.com/cgi/imok/imok.cgi?command=set_password&user_id=<%user_id%>&set_password_code=<%set_password_code%>
    );
my $path_to_users = $AuthorizeMeObj->{'settings'}->{'path_to_users'} = './users/';
$AuthorizeMeObj->{'settings'}->{'path_to_tokens'} = './tokens/';
$AuthorizeMeObj->{'settings'}->{'path_to_authorizations'} = './authorizations/';

$AuthorizeMeObj->{'settings'}->{'max_failed_attempts'} = 3; #password
$AuthorizeMeObj->{'settings'}->{'lock_time'} = 15;#in minutes

my $test_email_template;
my $imnotok_email_template;
my $pre_warn_email_template;

my $email_list;

my $message = '';

eval { &main(); };     # Trap any fatal errors so the program hopefully
if ($@) { &cgierr("fatal error: $@"); }     # never produces that nasty 500 server error page.
exit;   # There are only two exit calls in the script, here and in in &cgierr.

sub make_email_list(){
  my $user = shift;
  my @email_list = ($user->{'email'},$user->{'email_contact_1'},$user->{'email_contact_2'},$user->{'email_contact_3'});
  @email_list = grep /\S/, @email_list; #remove blank email entries
  my $email_list = join(',' , @email_list);
  return $email_list;
}

sub main(){
#create required directories if they do not exist
my @directories = ('authorizations' , 'tokens' , 'users');
foreach my $directory (@directories){
   unless(-e $directory or mkdir $directory) {
          die "Unable to create $directory\n";
      }
}

$pre_warn_email_template = qq(Your IMOK alert will be sent soon. You should push the IMOK button at: https://www.emogic.com/cgi/imok/imok.cgi.); #needs to be BEFORE we run cron
if ( $ARGV[0] eq 'cron' ) { &cron(); exit;} #from cron so exit after processing

%in = &parse_form();
my $command = $in{'command'};
&write_to_log("Parsed command: $command");

my $output = '';
$output = &get_template_page('main.html');

&write_to_log("Loaded template main");

my $logged_in = $AuthorizeMeObj->AmILoggedIn();
my $user = $AuthorizeMeObj->{'user'}; #local copy of user

&write_to_log("checked login");

$email_list = &make_email_list($user);
$test_email_template = qq(This email was sent by the IMOK system as a test by $AuthorizeMeObj->{'user'}->{'email'} . Please let them know you received it.);
$imnotok_email_template = qq($AuthorizeMeObj->{'user'}->{'email'} has pushed the IM_NOT_OK button. Please check on them.);

&write_to_log("built email list: $email_list");

my $result = 0;
if ( $logged_in ) {#we are logged in
    &write_to_log("logged in");
    if ( $command eq 'logout' ) { $logged_in = &logout() } #login email , password
    if ( $command eq 'logout_all_devices' ) { $logged_in = &logout_all_devices() }
    if ( $command eq 'reset_password' ) { &reset_password($in{'current_password'} , $in{'new_password'}); }
    #if ( $command eq 'get_settings' ) { &get_settings(\$output) }
    if ( $command eq 'get_settings' ) { $output = &get_settings($user) }
    if ( $command eq 'set_settings' ) {
      &set_settings();
      $user = $AuthorizeMeObj->{'user'};#get changes that were saved. may need these below
      #mail message
      $AuthorizeMeObj->{'settings'}->{'email_to'} = $user->{'email'};
      $AuthorizeMeObj->{'settings'}->{'email_subject'} = 'IMOK Settings Changed';#provide later
      $AuthorizeMeObj->{'settings'}->{'email_message'} = "Your IMOK Settings have been changed.<br>Access site at: https://www.emogic.com/cgi/imok/imok.cgi";
      $AuthorizeMeObj->email();
      }
    if ( $command eq 'imok' ) { &imok() }
    if ( $command eq 'imnotok' ) { &imnotok() }
    if ( $command eq 'testimok' ) { &testimok() }
    if ( $command eq 'delete_account' ) { $logged_in = ! &delete_account() }
    }
else{#we are not logged in
    &write_to_log("not logged in");
    if ( $command eq 'register' ) { &register(); } #load register form from ./forms/register.html or just jump to it?
				if ( $command eq 'activate' ) { &activate($in{'activate_code'} , $in{'user_id'}) } #login email , password
    if ( $command eq 'login' ) {
      $logged_in = &login();
      $user = $AuthorizeMeObj->{'user'};
    } #login email , password
    if ( $command eq 'forgot_password' ) { &forgot_password($in{'email'}) }
    if ( $command eq 'set_password' ) { &set_password($in{'user_id'} , $in{'set_password_code'}); }#from link sent by &forgot_password
    }

my $welcome = qq|
<p>Welcome to IMOK, and your first login. Please set up your first alert with the settings below.</p>
|;

if(  ($logged_in == 1) && ($user->{'first_login'} == 1) ) {#force user to see settings page
       #$output = &get_template_page("welcome.html");
       $output = &get_settings($user);
       $output =~ s/<%welcome%>/$welcome/g; #first welcome for settings page
      }
else{
 $output =~ s/<%welcome%>//g; #blank welcome for settings page on all other visits
}

if ( $command eq 'cron' ) { &cron() } #so we can trigger it web

if ( $logged_in ) {#we are logged in from cookie token or login routine
    #send trigger time to the js in main.html
    my $filename = "$AuthorizeMeObj->{'settings'}->{'path_to_users'}$user->{'user_id'}";
    my $trigger_time = &get_time_stamp($filename);
    $output =~  s/<%trigger_time%>/$trigger_time/g; #for main page  != 0

     # my $check_in_date = $user->{'start_date'}; #WRONG should be timestamp
     my $check_in_date = scalar localtime($trigger_time); #WRONG should be timestamp
     #my $check_in_time = $user->{'start_time'};
     $output =~  s/<%check_in_date%>/$check_in_date/g;
     #$output =~  s/<%check_in_time%>/$check_in_time/g;
     $output =~  s/<%check_in_time%>//g;

    $output =~ s/<%logged_out%>/hide_me/g; #hide login, register , forgot pw
    $output =~ s/<%logged_in%>/show_me/g; #show logout, settings, reset pw
    }
else{
    $output =~ s/<%logged_out%>/show_me/g; #show login, register , forgot pw
    $output =~ s/<%logged_in%>/hide_me/g; #hide logout, settings, reset pw
    }

&write_to_log("ready to print");
my $AuthMessage = $AuthorizeMeObj->get_message();
$message = "$message<br>$AuthMessage";
$output =~  s/<%last_message%>/$message/g;
my $set_cookie_string = $AuthorizeMeObj->get_set_cookie_string();
#print "Status: 303\n";
#print "Location: ./login.html\n";
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

	my $now = time();
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = gmtime($now);
$mon = $mon + 1;
$year = 1900 + $year;
my $time_string = sprintf("%d-%.2d-%.2d  %d:%.2d", $year , $mon , $mday , $hour , $min);

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
 print FH "$time_string: $text\n";
 close(FH);
 return 1;
}

sub imok(){
my $logged_in = $AuthorizeMeObj->AmILoggedIn();
my $user = $AuthorizeMeObj->{'user'};
if( ! $logged_in ){return 0;}
my $filename = "$AuthorizeMeObj->{'settings'}->{'path_to_users'}$user->{'user_id'}";
my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$current_time_stamp,$ctime,$blksize,$blocks) = stat($filename);
#my $new_time_stamp = $current_time_stamp; #will ALWAYS jump to next start_time (after now) + timeout

#my $new_time_stamp = $user->{'start_unix_time'}; #will ALWAYS jump to next start_time (after now) + timeout
my $new_time_stamp = $current_time_stamp; #will ALWAYS jump to next start_time (after now) + timeout

my $now = time();

if( $current_time_stamp <= $now ){#alarm was/is triggered
  until( $new_time_stamp  > $now ){#we do this loop as we are basing our repeating Alert date/times based on our initial setting, not based on when we click the imok button
   $new_time_stamp = $new_time_stamp + $user->{'timeout_sec'};
  }
 $message = "$message Alarm was likely triggered. Please email your contacts and tell them you are OK.";
 #send out IMOK email. Member has checked in...
}
elsif( ($current_time_stamp - $user->{'timeout_sec'}) <= $now ){ #we are clicking just before alarm is triggered
 until( $new_time_stamp  > ($now + $user->{'timeout_sec'}) ){
   $new_time_stamp = $new_time_stamp + $user->{'timeout_sec'};
  }
}
elsif( ($current_time_stamp - $user->{'timeout_sec'}) > $now  ){# we are a full timeout before the time stamp. do nothing
  return 1;
}#do nothing

#trigger time on users computer
my $new_time_stamp_user_tz = $new_time_stamp + ($user->{'tz_offset_hours' } * 60 * 60);
my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = gmtime($new_time_stamp_user_tz);
$mon = $mon + 1;
$year = 1900 + $year;
my $trigger_time_string = sprintf("%d-%.2d-%.2d  %d:%.2d", $year , $mon , $mday , $hour , $min);

my $result = &change_time_stamp($new_time_stamp , $filename);
if($result == 1){
 $message = "$message Trigger time updated.";
}
else{
 $message = "$message IMOK trigger time failed. Please try again.";
}
 &write_to_log("$user->{'email'} checked in.");
return $result;
}

sub imnotok(){
my $logged_in = $AuthorizeMeObj->AmILoggedIn();
my $user = $AuthorizeMeObj->{'user'};

$AuthorizeMeObj->{'settings'}->{'email_to'} = $email_list;
$AuthorizeMeObj->{'settings'}->{'email_subject'} = "IM(Not)OK Alert";
$AuthorizeMeObj->{'settings'}->{'email_message'} = $imnotok_email_template;
my $result = $AuthorizeMeObj->email();
&write_to_log("sendmail result : $result : $user->{'email_contact_1'} : $user->{'email'}");
$message = "$message sendmail result : $result : $user->{'email_contact_1'} : $user->{'email'} : $imnotok_email_template ";
}

sub testimok(){
 $AuthorizeMeObj->{'settings'}->{'email_smtp_server'} = 'mail.emogic.com'; #mail.emogic.com
 $AuthorizeMeObj->{'settings'}->{'email_smtp_port'} = '26'; #26

  my $logged_in = $AuthorizeMeObj->AmILoggedIn();
  my $user = $AuthorizeMeObj->{'user'};
  my $result;

  $AuthorizeMeObj->{'settings'}->{'email_to'} = $email_list;
  $AuthorizeMeObj->{'settings'}->{'email_subject'} = "IMOK Test Email";
  $AuthorizeMeObj->{'settings'}->{'email_message'} = $test_email_template;
  $result = $AuthorizeMeObj->email();

  &write_to_log("sendmail result : $result : $user->{'email_contact_1'} : $user->{'email'}");

  $message = $AuthorizeMeObj->get_message();
  $message = "mail result : $result : To: $email_list : $test_email_template";
}

sub cron(){
  &write_to_log("start of cron");
  my @filenames = glob("$path_to_users*");#get the list of files in the users directory
  foreach my $filename (@filenames){
   #$message = '';
    &write_to_log("Looking at $filename");
				my $user = $AuthorizeMeObj->db_to_hash($filename); #open file get details
    $email_list = &make_email_list($user);
    my $timestamp = &get_time_stamp($filename);

    my $t = time();
    &write_to_log("Time is $t and timestamp is $timestamp and pretime is $user->{'pre_warn_time'} and last email sent at $user->{'last_email_sent_at'}");

    if( ( time() > ($timestamp - $user->{'pre_warn_time_sec'}) ) && ($timestamp > time()) ){#send prewarn email to self
         $AuthorizeMeObj->{'settings'}->{'email_to'} = $user->{'email'};
         $AuthorizeMeObj->{'settings'}->{'email_subject'} = "IMOK Pre Alert";
         #$AuthorizeMeObj->{'settings'}->{'email_message'} = "$pre_warn_email_template <p> Alert was sent on behalf of $user->{'email'} </p>";
         $AuthorizeMeObj->{'settings'}->{'email_message'} = $pre_warn_email_template;
         my $result = $AuthorizeMeObj->email();
         }
    if($timestamp > time()){
       next;
       }#we are not alarming
    if(defined $user->{'last_email_sent_at'}){
      if($user->{'last_email_sent_at'} > (time()-(60 * 60)) ){
         next;
      }#we are waiting an hour before sending another alert email!
    }

    # &write_to_log("Result of user db $result user $user->{'user_id'}");
    #send alert emails
    $AuthorizeMeObj->{'settings'}->{'email_to'} = $email_list;
    $AuthorizeMeObj->{'settings'}->{'email_subject'} = "IMOK Alert";
    $AuthorizeMeObj->{'settings'}->{'email_message'} = "$user->{'email_form'} <p> Alert was sent on behalf of $user->{'email'} </p>"; #add users email at end of message in case they do not provide any identification in the email
    #my $uu = $AuthorizeMeObj->{'settings'}->{'email_message'} ;
    my $result = $AuthorizeMeObj->email();
    &write_to_log("sendmail result : $result : $user->{'email_contact_1'} : $user->{'email'}");
    #$user->{'timestamp'} = (60 * 60) + $timestamp; #set time stamp ahead one hour. So we do not send an email for another hour

    #$user->{'last_email_sent_at'} = time();
    #$user->{'alerts_sent'} = 1 + $user->{'alerts_sent'};  #increase email file count
    #$AuthorizeMeObj->hash_to_db($user , $filename); #save file
    #&change_time_stamp($timestamp , $filename);#restore old time stamp : so db update does not change it.

    #$message = "$message $AuthorizeMeObj->{'settings'}->{'email_message'}";
    &write_to_log("$filename Alert to $email_list at $t :  $AuthorizeMeObj->{'settings'}->{'email_message'}");
    }
&write_to_log("end of cron");
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
  my $filename = shift;
  my $output = '';
  open(FH, '<', "$path_to_templates/$filename") or die $!;
  while(<FH>){
   $output = $output . $_;
  }
  close FH;
  return $output;
}

sub get_settings(){ #input user, output html
 my $user = shift;
 my $output = &get_template_page('settings.html'); #string passed by ref so we can modify it
 #replace tokens
 $output =~ s/<%email_contact_1%>/$user->{'email_contact_1'}/g;
 $output =~ s/<%email_contact_2%>/$user->{'email_contact_2'}/g;
 $output =~ s/<%email_contact_3%>/$user->{'email_contact_3'}/g;
 $output =~  s/<%email_form%>/$user->{'email_form'}/g;
 $output =~  s/<%timeout%>/$user->{'timeout'}/g;
 $output =~  s/<%start_date%>/$user->{'start_date'}/g;
 $output =~  s/<%start_time%>/$user->{'start_time'}/g;
	$output =~  s/<%pre_warn_time%>/$user->{'pre_warn_time'}/g;

 return $output;
}

sub set_settings(){
my $logged_in = $AuthorizeMeObj->AmILoggedIn();
my $user = $AuthorizeMeObj->{'user'};
if(! $logged_in){ return 0; }
$user->{'first_login'} = 0; #clear this
my $email = $in{'email_contact_1'};
$email =~ s/^\s+|\s+$//g; #trim email
if(($email eq '') || ($AuthorizeMeObj->valid_email($email))){
  $user->{'email_contact_1'} = $email;
 }
 else{
  $message = "$message : $email is not a valid email address. Go back to settings and enter a valid email address.";
  return 0;
 }
 $email = $in{'email_contact_2'};
 $email =~ s/^\s+|\s+$//g; #trim email
 if(($email eq '') || ($AuthorizeMeObj->valid_email($email))){
  $user->{'email_contact_2'} = $email;
 }
 else{
  $message = "$message : $email is not a valid email address. Go back to settings and enter a valid email address.";
  return 0;
 }
 $email = $in{'email_contact_3'};
 $email =~ s/^\s+|\s+$//g; #trim email
 if(($email eq '') || ($AuthorizeMeObj->valid_email($email))){
  $user->{'email_contact_3'} = $email;
 }
 else{
  $message = "$message : $email is not a valid email address. Go back to settings and enter a valid email address.";
  return 0;
 }

 $user->{'email_form'} = $in{'email_form'};
 $user->{'email_form'} =~ s/\r//g; #fix windows from adding extra lines

 $user->{'timeout'} = $in{'timeout'};
 $user->{'timeout_sec'} = 24 * 60 * 60 * $in{'timeout'};
	$user->{'pre_warn_time'} = $in{'pre_warn_time'};
 $user->{'pre_warn_time_sec'} = 60 * 60 * $in{'pre_warn_time'};
 $user->{'last_email_sent_at'} = 0;

	$user->{'start_date'} = $in{'start_date'};
 $user->{'start_time'} = $in{'start_time'};

 #why was all this here. timestamp duplication?
 #no use file timestamp only
 #if( $in{'timestamp'} eq "NaN" ){
  #  $in{'timestamp'} = time();
 #}
 #$user->{'start_unix_time'} = $in{'timestamp'};
 #$user->{'timestamp'} = $in{'timestamp'}; #generated by JS on settings.html page and based on Alert time and date

 $user->{'tz_offset_hours'} = $in{'tz_offset_hours'};

 my $user_id = $AuthorizeMeObj->get_user_id();  #get_user_id

 my $filename = "$path_to_users$user_id";
 my $result = $AuthorizeMeObj->hash_to_db($user , $filename);
 $AuthorizeMeObj->{'user'} = $user; #save it back to object as hash_to_db does not

  if($result == 1){
  $message = "$message Your Alert has been set. Verify the alert date and time. You can then close this program or leave it open. Open it again when you want to push the IMOK button.";
  }
 else{
  $message = "$message Your Alert has not been set.";
  }

 my $hour_seconds = 60 * 60;
 my $day_seconds = 24 * $hour_seconds;

 #my $timestamp = $user->{'timestamp'}; #trigger timestamp based on PC's local time
 my $timestamp = $in{'timestamp'}; #generated by JS on settings.html page and based on Alert time and date #Alert timestamp based on PC's local time
 $result = &change_time_stamp($timestamp , "$path_to_users$user->{'user_id'}");
 if($result == 0){
  $message = "$message Could not set timestamp on $path_to_users$user->{'user_id'}";
  }

 #my @lt = localtime($timestamp);
 #my $str_time = sprintf("%d:%.2d", $lt[2] , $lt[1]);
 #my $year = 1900 + $lt[5];
 #my $month = $lt[4] + 1;
 #$message = "$message Trigger time is $year-$month-$lt[3] $str_time on the server and $in{'start_date'} $in{'start_time'} local time on your pc";

 return $result;
}

sub register() {
	my $email = lc $in{'email'};#note email coveted to lower case!
	my $password = $in{'password'};
	my $result = $AuthorizeMeObj->register_account($email , $password);
 if($result == 0){
    $message = "$message<br>Your registration failed."
  }
 else{
      $message = "You have registered for an IMOK account. Please check your email, and click on the link within, to activate your account.";
 }
 return $result;
}

sub activate(){
 my $authorize_code = shift;
 my $user_id = shift;

 my $user =  $AuthorizeMeObj->activate_account( $authorize_code , $user_id );
 if(!defined($user)) {$message = "$message Your activation failed."; return 0};

 $user->{'email_contact_1'} = '';
 $user->{'email_contct_2'} = '';
 $user->{'email_contact_3'} = '';
 $user->{'email_form'} = qq("Type your name here" has not reported in to the IMOK website by the chosen time.
You may want to check on them.
Their phone number is xxx-xxx-xxxx.
Their email address is type_your_email_here\@domain
Their address is 15 Gravel Ave, Old Town, Ontario, Canada, L0M 1N0

They have pets.
');
 $user->{'timeout'} = 1; # 1 day
 #$user->{'timeout_sec'} = 60 * 60 * 24;
 $user->{'pre_warn_time'} = 1; #1 hour
 #$user->{'pre_warn_time_sec'} = 60 * 60 ;
 my $now = time();
 #?? need?
 #$user->{'timestamp'} = time() + $user->{'timeout_ms'}; #set a default of 1 day
 $user->{'first_login'} = 1;
 $user->{'failed_attempts'} = 0;

 my $filename = "$path_to_users$user->{'user_id'}";
 my $result =  $AuthorizeMeObj->hash_to_db($user , $filename);
 &change_time_stamp($user->{'timestamp'} , $filename);#update time stamp

 if($result == 1){
  $message = "$message Your account for $user->{'email'} has been activated. Please log in and complete your setup.";
  }
 else{
  $message = "$message Error: Your account $user->{'email'} could not be authorized";
  }
 return $result;
 }

sub login(){
 #email points to data file
 #trim inputs. portable devices are easy to add and not notice them
 $in{'email'} =~ s/^\s+|\s+$//g;
 $in{'password'} =~ s/^\s+|\s+$//g;
  my $result =  $AuthorizeMeObj->login( lc $in{'email'} , $in{'password'} );#note email coveted to lower case!

 my $user = $AuthorizeMeObj->{'user'};
 if($result == 1){
  $message = "$message $user->{'email'} has logged in";
  }
 else{
  $message = "$message $user->{'email'} could not log in";
  }
 return $result;
}

sub logout(){
 my $result =  $AuthorizeMeObj->logout();
 my $user = $AuthorizeMeObj->{'user'};
 if($result == 1){
  $message = "$message $user->{'email'} has logged out";
  }
 else{
  $message = "$message $user->{'email'} could not log out";
  }
 return ! $result;
 }

sub logout_all_devices(){
 my $result =  $AuthorizeMeObj->logout_all_devices();
 my $user = $AuthorizeMeObj->{'user'};
 if($result == 1){
  $message = "$message $user->{'email'} has logged out of all devices";
  }
 else{
  $message = "$message $user->{'email'} could not log out of all devices";
  }
 return ! $result;
}

sub delete_account(){
 my $user = $AuthorizeMeObj->{'user'};
 my $result =  $AuthorizeMeObj->delete_account();
 if($result == 1){
  $message = "$message $user->{'email'} has deleted their account";
  }
 else{
  $message = "$message $user->{'email'} could not delete their account";
  }
 return $result;
}

sub forgot_password(){
 &write_to_log("For");
 my $email = shift;
 my $result = $AuthorizeMeObj->forgot_password($email);
 if($result == 1){
  }
 else{
  $message = "$message $email could not recover password";
  }
 return $result;
}

sub set_password(){
 my $user_id = shift;
 my $set_password_code = shift;
 my $result = $AuthorizeMeObj->set_password($user_id,$set_password_code);
 if($result == 1){
  $message = "$message Password was reset";
  }
 else{
  $message = "$message Password was not reset";
  }
 return $result;
}

sub reset_password(){
 my $current_password = shift;
 my $new_password = shift;
 my $result = $AuthorizeMeObj->reset_password($current_password,$new_password);
 if($result == 1){
  $message = "$message Password was reset";
  }
 else{
  $message = "$message Password was not reset";
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
