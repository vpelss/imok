package AuthorizeMe ; 

use strict;
use Socket;
use Fcntl;   # For O_RDWR, O_CREAT, etc.
use Data::Dumper;
use Digest::SHA qw(sha1_base64 sha1_hex sha512_base64);
#use vars qw($NAME $ABSTRACT $VERSION);
our ($NAME , $ABSTRACT , $VERSION);

$NAME     = 'AutorizeMe';
$ABSTRACT = 'AutorizeMe Module for Simple CGI Registration & Authentication in Perl';
$VERSION  = '0.2'; 

#require Exporter;
our @ISA = qw(Exporter);
our @EXPORT = qw(  );

#manages token cookie
#manages db read and write, can add fields!!!!!
#manages mailing
#DOES NOT manage forms and log in, reset, log out logic

my $user = \{}; #meta ref to db hash of user structure provided by calling program at new(\%user) so $user->{}. calling program simply accesses it's %user after module has updated it
my $AuthorizeMe_Settings; #ref to hash, sent from calling program
 
my $cookies; #will be a ref to a anonymous hash
my $email;
my $user_id; #made from $email
my $token;
my $random_number_size = 1000000000;
my $set_cookie_string = ""; #calling program can use get_set_cookie_string
my $last_message = ''; #used for &get_last_message()

#determined by calling program. we are a module and code is inaccessible?
my $path_to_users; 
my $path_to_tokens;  
my $from_email; 
my $SEND_MAIL = '';
my $SMTP_SERVER = '';
my $token_name = "AuthorizeMeToken";
my $user_id_name = "AuthorizeMeUserId";
my $MaxAge = '3153600000'; #default 100 years, in case not supplied in new()

sub new() { #init + see if we have a valid auth token and a valid  user file
  my $class = shift;   
  $user = shift; #hash reference kept as we want two way communication
  $AuthorizeMe_Settings = shift; 
 
  #setup settings from calling program
  $from_email = $AuthorizeMe_Settings->{'from_email'};
  $SEND_MAIL = $AuthorizeMe_Settings->{'sendmail'}; 
  $SMTP_SERVER = $AuthorizeMe_Settings->{'smtp_server'}; 
  $path_to_users =  $AuthorizeMe_Settings->{'path_to_users'}; 
  $path_to_tokens = $AuthorizeMe_Settings->{'path_to_tokens'}; 
  #$user_file_extension = $AuthorizeMe_Settings->{'user_file_extension'}; 
  if($AuthorizeMe_Settings->{'token_name'}){ $token_name = $AuthorizeMe_Settings->{'token_name'}; }
  if($AuthorizeMe_Settings->{'user_id_name'}) { $user_id_name = $AuthorizeMe_Settings->{'user_id_name'}; }
  if($AuthorizeMe_Settings->{'token_max-age'}) { $MaxAge = $AuthorizeMe_Settings->{'token_max-age'}; }
  
  $cookies = &get_cookies();
  $token = $cookies->{$token_name}; #does the client think they are logged in?
  $user_id = $cookies->{$user_id_name};

  my $self = {
    #logged_in => $logged_in,
    #user_email  => $user_email
    };
 
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
    
    my $email_message = $AuthorizeMe_Settings->{'registration_email_template'};
    $email_message =~ s/<%activate_code%>/$random_number/g;
    
    #send email message
    sendmail($from_email , $from_email , $email , $SEND_MAIL , 'IMOK account activation email' , '');
    
    #return success with message stating auth email must be clicked!
    $last_message = "You have been registered, but must activate your account by clicking on the link in the email sent to $email :  $email_message";
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
  #make sure we set a global $email and save $tokens as AmILoggedIn will need this
  shift;
  $email = shift;
  my $password = shift;
  $user_id = &create_user_id($email); #user id is hash of email
  my $logged_in;
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
      if(@the_keys >= 10){#limit # of tokens to 10
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

 $set_cookie_string = "Set-Cookie: $token_name= ; Max-Age=-1 ;\nSet-Cookie: $user_id_name= ; Max-Age=-1 ;";
 return $result;
 }
  
sub get_set_cookie_string(){
  return $set_cookie_string;
  }
  
sub reset_password(){
 
 }

sub forgot_password(){
 my $result = 0;
 shift;
 my $email = shift;
 #check email
 if(&valid_email($email) != 1){
  $last_message = "Invalid Email $email";
  return 0;
 }
 #check user_id : exists?
 my $user_id = &create_user_id($email);
 my $filename = $user_id;
 $filename = "$path_to_users$filename";
 if(! -e $filename){
  $last_message = "User does not exist for $email";
  return 0;  
 }
 #set auth_file named $user_id: will contain random forgot_password_set_id
  my $random_number = int(rand($random_number_size)); #acts as both auth code and new password
  $filename = "$AuthorizeMe_Settings->{'path_to_authorizations'}$user_id";  
  $result = &hash_to_db({password_code => $random_number} , $filename);
  if($result != 1){
    $last_message = "could not save to $filename";
    return 0;
  } 
 #send email with link ?command=forgot_password_set&forgot_password_set_id=????????????
 my $email_message = $AuthorizeMe_Settings->{'forgot_password_email_template'};
 $email_message =~ s/<%set_password_code%>/$random_number/g;
 $email_message =~ s/<%user_id%>/$user_id/g;
 #send email message
 sendmail($from_email , $from_email , $email , $SEND_MAIL , 'IMOK account activation email' , '');
 
 $last_message = "Your password recovery email has been sent to $email : $email_message";
 return 1;
 }

sub set_password(){
 #if($_[0] eq $NAME){shift}; #so we can call from inside module or outside
 shift;
 my $user_id = shift;
 my $set_password_code = shift;
 my $filename = "$AuthorizeMe_Settings->{'path_to_authorizations'}$user_id";
 my $hash_auth_ref = {};
 my $result = &db_to_hash($hash_auth_ref , $filename);
 my $set_password_code_stored = $hash_auth_ref->{'password_code'};
 if($result != 1){
    $last_message = "could not open $filename";
    return 0;
  }
 if($set_password_code != $set_password_code_stored){
  $last_message = "codes do not match";
  return 0;
 }
 $result = 1;
 #change password and store it
 my $filename2 = "$path_to_users$user_id";
 $result = &db_to_hash($user,$filename2);
 if($result != 1){
    $last_message = "could not open $filename2";
    return 0;
  }
 my $encrypted_password = &encrypt_password($set_password_code_stored);
 $user->{'password'} = $encrypted_password;
 $result = &hash_to_db($user,$filename2);
 if($result != 1){
    $last_message = "could not save $filename2";
    return 0;
  }
 #delete code file
 $result = unlink $filename;
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