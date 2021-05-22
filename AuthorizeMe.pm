package AuthorizeMe ; 

use strict;
use Socket;
#use CGI::Cookie;
use Fcntl;   # For O_RDWR, O_CREAT, etc.
#use SDBM_File;
#use GDBM_File;
#use YAML::old;
use Data::Dumper;
use Digest::SHA qw(sha1_base64 sha1_hex sha512_base64);
#use vars qw($NAME $ABSTRACT $VERSION);
our ($NAME , $ABSTRACT , $VERSION);

$NAME     = 'AutorizeMe';
$ABSTRACT = 'AutorizeMe Module for Simple CGI Registration & Authentication in Perl';
$VERSION  = '0.1'; # Last update: 

#require Exporter;
our @ISA = qw(Exporter);
our @EXPORT = qw(  );

#manages token cookie
#manages db read and write, can add fields!!!!!
#manages mailing
#DOES NOT manage forms and log in, reset, log out logic
 
my $cookies; #ref to a anonymous hash
my $token;
my $user_id;
my $random_number_size = 1000000000;

#determined by calling program. we are a module and code is inaccessible?
my $path_to_users; #set from calling program
my $path_to_tokens; #set from calling program
my $user_file_extension; #set from calling program

my $logged_in;
my $token_name = "AuthorizeMeToken";
my $user_id_name = "AuthorizeMeUserId";
my $MaxAge = '3153600000'; #default 100 years, in case not supplied in new()
#my $token_value; #token file will contain email
my $set_cookie_string = ""; #calling program can use / print this start with '' then on login: "Set-cookie: $name=$value; date=$cur_date; expires=$expires_date path=$path; domain=$domain"
my $domain;

my  $last_message = ''; #used for &get_last_message()

my $user = \{}; #meta ref to db hash of user structure provided by calling program at new(\%user) so $user->{}. calling program simply accesses it's %user after module has updated it
my $from_email; #set in new by calling program 
my $SEND_MAIL = '';
my $SMTP_SERVER = '';

sub new() { #init + see if we have a valid auth token and a valid  user file
  my $class = shift; #check on this!!!!!!!!!!!!   
  $user = shift; #hash reference kept as we want two way communication
  my %AuthorizeMe_Setup = %{shift(@_)}; #one way communication
  
  #setup settings from calling program
  $from_email = $AuthorizeMe_Setup{'From_Email'};
  $SEND_MAIL = $AuthorizeMe_Setup{'SEND_MAIL'}; 
  $SMTP_SERVER = $AuthorizeMe_Setup{'SMTP_SERVER'}; 
  $path_to_users =  $AuthorizeMe_Setup{'path_to_users'}; 
  $path_to_tokens = $AuthorizeMe_Setup{'path_to_tokens'}; 
  $user_file_extension = $AuthorizeMe_Setup{'user_file_extension'}; 
  if($AuthorizeMe_Setup{'Token_Name'}){ $token_name = $AuthorizeMe_Setup{'Token_Name'}; }
  if($AuthorizeMe_Setup{'User_ID_Name'}) { $user_id_name = $AuthorizeMe_Setup{'User_ID_Name'}; }
  $domain = $AuthorizeMe_Setup{'domain'};
  if($AuthorizeMe_Setup{'Token_Max-Age'}) { $MaxAge = $AuthorizeMe_Setup{'Token_Max-Age'}; }
  
  $cookies = &get_cookies();
  $token = $cookies->{$token_name}; #does the client think they are logged in?
  $user_id = $cookies->{$user_id_name};
  
  $logged_in = AmILoggedIn();

  my $self = {
    #logged_in => $logged_in,
    #user_email  => $user_email
    };
  #build $self from $user (ref to arg %)
 
  bless $self, $class;
  return $self;  
}

sub get_cookies(){
  my %local_cookies;
  my $cookie = $ENV{HTTP_COOKIE};
  my @all = split(/\;/, $cookie);
  foreach (@all) { # fill in %cookies
    $_ =~ s/^\s+|\s+$//g; #trim  leading and lagging white space of cookie. a must for multiple cookies 
    (my $var, my $value) = split(/=/);
    $local_cookies{$var} = $value;
    }
  return \%local_cookies;
}

sub set_cookies(){ #take a ref to $cookies hash : set_cookies($cookie_name,$cookie_value,$cookie_expire,$cookie_path,$cookie_domain)
 my $cookie_name = shift;
 my $cookie_value = shift;
 my $cookie_expire = shift; #in seconds
 my $cookie_path = shift;
 my $cookie_domain = shift;
 
 #Set-Cookie: id=a3fWa; Expires=Wed, 21 Oct 2015 07:28:00 GMT
  my @months = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
 my @days = qw(Sun Mon Tue Wed Thu Fri Sat Sun);
 my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);                                            
 my $cur_date = "$days[$wday], $mday $mon $year $hour:$min:$sec";

 ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time + $cookie_expire);                                            
 my $expires_date = "$days[$wday], $mday $mon $year $hour:$min:$sec";

 ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
 print "$mday $months[$mon] $days[$wday]\n";

 #print "Content-type: text/html\n\n";
 return "Set-cookie: $cookie_name=$cookie_value; date=$cur_date; expires=$expires_date path=$cookie_path; domain=$cookie_domain";
 }

sub hash_to_db(){#arg: \%hash , $filename
  #iterate through all keys and copy to db_hash
  my $hash_ref = shift;
  my $filename = shift;
   
  #open(FH, '>', $filename) or die $!;
  open(FH, '>', $filename) or return 0;# $!;
  print FH Data::Dumper->Dump([$hash_ref], [qw(dump_hash_ref)]); # $dump_hash_ref is the variable name in the dump
  close(FH);

  return 1;
}

sub db_to_hash(){#arg \%hash , $filename
  my $hash_ref = shift;
  my $filename = shift;
  my $string = '';
  my @string;
  
  open(FH, '<', $filename) or return 0;# $!;
  while(<FH>){
    $string = "$string$_";
    }
  close(FH);

  my $dump_hash_ref = {}; #$dump_hash_ref is the var name in the Dump
  $dump_hash_ref = eval $string;
  
  #copy back to global hash ref
  foreach my $key (keys %{$dump_hash_ref}) {
    #$user->{$key} = $dump_hash_ref->{$key}; #$user is a reference, so we deference to copy to it
    $hash_ref->{$key} = $dump_hash_ref->{$key}; #$user is a reference, so we deference to copy to it
    }
  
  return 1;
}

sub get_last_message(){
  return $last_message;    
}

sub AmILoggedIn(){
  my $result = 0;
  
  my $filename = "$path_to_tokens$user_id";
  if( -e $filename ){ #tokens file exists
    my $tokens = {};
    &db_to_hash($tokens , $filename); #we are clobbering $user, but we reset it later. Maybe use another hash ref?
    if( $tokens->{$token} == 1 ){#does the token exist?
     $filename = "$path_to_users$user_id";
     if(-e $filename){ #also see if user file exists
      $result = 1;
     }
    }
 return $result; 
 }
}

sub create_user_id(){
 my $email = shift; 
 my $user_id = sha1_base64($email); #user id is hash of email
 $user_id =~ s/[^a-zA-Z0-9,]//g; # remove all non alphanumeric characters
 return $user_id;
}
 
sub register_account()
    { #get data
    shift; #remove module #
    #my $username = shift; 
    my $email = shift; 
    $email =~ s/\A\s\Z//g; #remove white space
    
    my $password = shift;
    $password =~ s/\s\W//; #no white space, only alpha numeric
    if($password eq ""){
      $last_message = "Your password cannot be empty";
      return 0;
    }
      
    if( ! valid_email($email) ){ #check for valid email
      $last_message = 'Invalid Email Address';
      return 0;
      }
    
    my $user_id = &create_user_id($email); #user id is hash of email
    
    #see if  user file exists, fail if it does, pass message?
     my $filename = "$path_to_users$user_id"; 
    if(-e $filename){
      $last_message = "This Email Address is already registered : $email";
      return 0;
      }
    
    # $user->{'username'} = $username; #simplest case just use email as username also
    $user->{'email'} = $email;
    $user->{'user_id'} = $user_id; #also use as activate code
    #salt it up!!!!!!!!! with userid?
    my $password_hash = &encrypt_password($password);
    $user->{'password'} = $password_hash;
    $user->{'email_contact_1'} = '';
    $user->{'email_contct_2'} = '';
    $user->{'email_contact_3'} = '';
    $user->{'email_form'} = 'Member has not reported in to IMOK in a specified amount of time. You may want to check on them.';
    $user->{'timeout_ms'} = '86400000'; #24hours
    
    #save account data in file $random_number. when we ru
    my $random_number = int(rand($random_number_size));
    $filename = "$path_to_users$random_number";
    my $result = &hash_to_db($user , $filename);
    
    my $email_message = qq(You have registered for an IMOK account.
    Click to activate:
    http://127.0.0.1/cgi/imok/imok.cgi?command=activate&activate_code=$random_number
    );
    
    #send email message
    sendmail($from_email , $from_email , $email , $SEND_MAIL , 'IMOK account activation email' , '');
    
    #return success with message stating auth email must be clicked!
    $last_message = "You have been registered, but must activate your account by clicking on the link in the email sent to $email   $email_message";
      return 1;
          
    }

sub encrypt_password(){
  my $password = shift;
  #salt it up!!!!!!!!! with email?
  my $password_hash = sha512_base64($password);
  return $password_hash;
  }

sub activate(){
  shift;
  my $authorize_code = shift;
  my $new_filename = '';
  
  #does the file exist, rename to userid
  my $filename = "$path_to_users$authorize_code";
  my $result = &db_to_hash($user , $filename);
  if($result != 1){return 0}
  $new_filename = $user->{'user_id'};
  $new_filename = "$path_to_users$new_filename";
  $result = rename("$filename" , "$new_filename") ;
  return $result ;
  }

sub login() {
  #the only time we return is if we logged in and we do it silently as we use this every time script is run
  #return 1 on success and THEN check_login sends a text message on fail
  shift;
  my $email = shift;
  my $password = shift;
  my $user_id = &create_user_id($email); #user id is hash of email
  my $result;
  
  my $filename = $user_id;
  $filename = "$path_to_users$filename";
  if(-e $filename){
    $result = &db_to_hash($user , $filename); #get user data
    if($result != 1){return 0}
    my $encrypted_password_stored = $user->{'password'};
    my $encrypted_password = &encrypt_password( $password);
    if($encrypted_password eq $encrypted_password_stored){ 
     #set token
     $token = int(rand($random_number_size));
     #save token file    
     my $filename = "$path_to_tokens$user_id";
     my $tokens = {};
     if(-e $filename){ #does token file exist?
        $result = &db_to_hash($tokens , $filename);  # get existing tokens (ie: logon's on other devices)
      }
      my @the_keys = keys( %$tokens);
      my $len =  @the_keys;
      if(@the_keys >= 100){#limit # of tokens to 100
       delete( $tokens->{$the_keys[0]} ); #remove a token , first key
      }
     $tokens->{$token} = 1; #add token
     $result = &hash_to_db($tokens , $filename); #token file contains tokens of all logins!
     
     #how do we set cookie? just set $set_cookie_string : Set-Cookie: <cookie-name>=<cookie-value>
     #$set_cookie_string = &set_cookies($token_name , $token_value , &time() + 100000000 , '/' , $domain , '$cookie_time_zone' , '-00000');
     $set_cookie_string = "Set-Cookie: $token_name=$token; Max-Age=$MaxAge;\nSet-Cookie: $user_id_name=$user_id; Max-Age=$MaxAge;"; 
     #$set_cookie_string = "Set-Cookie: $token_name='$token', $user_id_name='$user_id'; Max-Age=$MaxAge ;"; 
     #$set_cookie_string = "Set-Cookie: $token_name='$token',$user_id_name='$user_id'; Max-Age=$MaxAge;"; 
     
     $last_message = "$user->{'email'} is logged in"; 
     $logged_in = 1; #let the world know we are logged in
     }
   else{
    $logged_in = 0;
    $set_cookie_string = '';
    $last_message = "Login for $user->{'email'} failed";
    $result = 0;
   }
  return $result ;
  }
 }
  
sub logout(){
 my $filename = "$path_to_tokens$user_id";
 my $tokens = {};
 my $result = &db_to_hash($tokens , $filename);  # get existing tokens (ie: logon's on other devices)
 delete $tokens->{$token};
 $result = &hash_to_db($tokens , $filename);  # get existing tokens (ie: logon's on other devices)

 $set_cookie_string = "Set-Cookie: $token_name= ; Max-Age=0 ;\nSet-Cookie: $user_id_name= ; Max-Age=0 ;";
 return $result;
 }
  
sub get_set_cookie_string(){
  return $set_cookie_string;
  }
  
sub reset_password()
    { #get data
=pod
     my $username = $in{'username'};
     $username =~ s/\s\W//; #no white space, only alpha numeric
     my $old_password = $in{'oldpassword'};
     my $new_password = $in{'newpassword'};
     $new_password =~ s/\s\W//; #no white space, only alpha numeric
     if ( $username eq '' or $old_password eq '' or $new_password eq '')
          { #form submit error
         &send_system_message("Blank fields are not allowed");
          }
     if (! -e "$path_to_users/$username$user_file_extension")
        { #file does not exist
        &send_system_message( "Username $username does not exists" );
        }
     else
          {
          my $crypt_old_password = crypt ($old_password , 'yum') ;
          open (FILE , "<$path_to_users/$username$user_file_extension");
          my @download = <FILE>;
          close FILE;
          chomp @download;
          my $passwordencrypted = $download[0];
          my $email = $download[1];
          if ($crypt_old_password eq $passwordencrypted)
               {
               #can change!!!
               open (FILE , ">$path_to_users/$username$user_file_extension");
               my $crypt_new_password = crypt ($new_password , 'yum') ;
               print FILE "$crypt_new_password\n";
               print FILE "$email\n";
               close FILE;
               &send_system_message( "Password changed for <font color=red><b>$username</b></font>." );
               }
          else
               {
               &send_system_message("Old Password incorrect.");
               }
          }
=cut
     }

sub forgot_password()
     { #get data
=pod
     my $username = $in{'username'};
     $username =~ s/\s\W//; #no white space, only alpha numeric
     if ( $username eq '')
          { #form submit error
          $message .= "Blank fields are not allowed";
          exit;
          }
     if (! -e "$path_to_users/$username$user_file_extension")
          { #file does not exist
          &send_system_message("Username $username does not exists");
          }
     else
          {
          my $new_password = rand(999999999);
          my $new_password_crypt = crypt ( $new_password  , 'yum') ;
          open (FILE , "<$path_to_users/$username$user_file_extension");
          my @download = <FILE>;
          close FILE;
          chomp @download;
          my $email = $download[1];
          open (FILE , ">$path_to_users/$username$user_file_extension");
          print FILE "$new_password_crypt\n";
          print FILE "$email\n";
          close FILE;
         if ( &valid_email($email) )
               {
               my $mail_message = "$username Your new password is $new_password.";
               my $result = &sendmail($FROM_MAIL, $SEND_MAIL, $email , $SMTP_SERVER, 'Your new Twixt password', $mail_message );
               if ( $result == 1 )
                    {
                    &send_system_message("Password changed for <font color=red><b>$username</b></font> and sent to <font color=red><b>$email</b></font>.");
                    }
               else
                    {
                     &send_system_message("Email error $result.");
                    }
               }
          else
               {
               &send_system_message("Email $email is not valid.");
               }
          }
=cut    
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

sub valid_email{
  my $username = qr/[a-z0-9_+]([a-z0-9_+.]*[a-z0-9_+])?/;
  my $domain   = qr/[a-z0-9.-]+/;
  #my $regex = $email =~ /^$username\@$domain$/;

  my $testmail = $_[0];
  if ($testmail =~/ /){ return 0; }
  #if ( $testmail =~ /(@.*@)|(\.\.)|(@\.)|(\.@)|(^\.)/ ||
  #$testmail !~ /^.+\@(\[?)[a-zA-Z0-9\-\.]+\.([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$/ )
  if ( $testmail !~ /^$username\@$domain$/ ){ return 0; }
  else { return 1; }
}

sub sendmail()
{#error codes below for those who bother to check result codes <gr>
# 1 success
# -1 $smtphost unknown
# -2 socket() failed
# -3 connect() failed
# -4 service not available
# -5 unspecified communication error
# -6 local user $to unknown on host $smtp
# -7 transmission of message failed
# -8 argument $to empty
#
#  Sample call:
#
# &sendmail($from, $reply, $to, $smtp, $subject, $message );
#
#  Note that there are several commands for cleaning up possible bad inputs - if you
#  are hard coding things from a library file, so of those are unnecesssary
#
    my ($fromaddr, $replyaddr, $to, $smtp, $subject, $message) = @_;

    $to =~ s/[ \t]+/, /g; # pack spaces and add comma
    $fromaddr =~ s/.*<([^\s]*?)>/$1/; # get from email address
    $replyaddr =~ s/.*<([^\s]*?)>/$1/; # get reply email address
    $replyaddr =~ s/^([^\s]+).*/$1/; # use first address
    $message =~ s/^\./\.\./gm; # handle . as first character
    $message =~ s/\r\n/\n/g; # handle line ending
    $message =~ s/\n/\r\n/g;
    $smtp =~ s/^\s+//g; # remove spaces around $smtp
    $smtp =~ s/\s+$//g;

    if (!$to)
    {
        return(-8);
    }

 if ($SMTP_SERVER ne "")
  {
    my($proto) = (getprotobyname('tcp'))[2];
    my($port) = (getservbyname('smtp', 'tcp'))[2];

    my($smtpaddr) = ($smtp =~
                     /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/)
        ? pack('C4',$1,$2,$3,$4)
            : (gethostbyname($smtp))[4];

    if (!defined($smtpaddr))
    {
        return(-1);
    }

    if (!socket(MAIL, AF_INET, SOCK_STREAM, $proto))
    {
        return(-2);
    }

    if (!connect(MAIL, pack('Sna4x8', AF_INET, $port, $smtpaddr)))
    {
        return(-3);
    }

    my($oldfh) = select(MAIL);
    $| = 1;
    select($oldfh);

    $_ = <MAIL>;
    if (/^[45]/)
    {
        close(MAIL);
        return(-4);
    }

    print MAIL "helo $SMTP_SERVER\r\n";
    $_ = <MAIL>;
    if (/^[45]/)
    {
        close(MAIL);
        return(-5);
    }

    print MAIL "mail from: <$fromaddr>\r\n";
    $_ = <MAIL>;
    if (/^[45]/)
    {
        close(MAIL);
        return(-5);
    }

    foreach (split(/, /, $to))
    {
        print MAIL "rcpt to: <$_>\r\n";
        $_ = <MAIL>;
        if (/^[45]/)
        {
            close(MAIL);
            return(-6);
        }
    }

    print MAIL "data\r\n";
    $_ = <MAIL>;
    if (/^[45]/)
    {
        close MAIL;
        return(-5);
    }

   }

  if ($SEND_MAIL ne "")
   {
     open (MAIL,"| $SEND_MAIL");
   }

    print MAIL "To: $to\n";
    print MAIL "From: $fromaddr\n";
    #print MAIL "Reply-to: $replyaddr\n" if $replyaddr;
    print MAIL "Subject: $subject\n";
    print MAIL qq|Content-Type: text/html; charset="iso-8859-1"
   Content-Transfer-Encoding: quoted-printable
   |
   ;
    print MAIL "\n\n";
    #print MAIL 'Mime-Version: 1.0'."\n";
    #print MAIL 'content-type:' . "text/HTML\n\n"; # <----------------- put the double \n\n here
    #print MAIL "Content-Transfer-Encoding: quoted-printable\n\n";

    print MAIL "$message";

    print MAIL "\n.\n";

 if ($SMTP_SERVER ne "")
  {
    $_ = <MAIL>;
    if (/^[45]/)
    {
        close(MAIL);
        return(-7);
    }

    print MAIL "quit\r\n";
    $_ = <MAIL>;
  }

    close(MAIL);
    return(1);
}

1; #module returns a win!