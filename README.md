# IMOK

# ABOUT

IMOK is a web based, fail safe, alarm that will email your family and friends if you don't check in.

Potential uses:

-For those living alone and do not have regular personal contact.
-For those who have animals or pets that may suffer or die if they pass away or became incapacitated.
-For those who live in a remote location.
-For those taking a trip alone.
-For those planning on getting kidnapped

# HELP

-Some options are accessed from the hamburger icon.
-After registering for an account, click on 'Settings'.
-Select a 'Check In Start Date' and a 'Check In Start Time' that you will be able to 'check in' by. 
-Select a 'Check In Interval'. Daily seems reasonable. 
-Add up to three email addresses to send alerts to. You must enter at least one.
-Modify the default alert message to suit your situation. Add contact numbers, instructions, etc...
-If you push the IMOK button before the 'Check In Time' no alert will be sent to your email list, and a new 'Check In Time' is set to the next 'Check In Interval'. 
-If you do not push the IMOK button before the 'Check In Time', an alert email will be sent to your email list every half hour until you push the IMOK button.
-If you push the IMNOTOK button an email alert is sent immediately to those in your email list. 

Example: If you choose a 'Check In Start Date' of 10 Sept 2021 and a 'Check In Start Time' of 9am and a 'Check In Interval' of one day, every time you push the IMOK button your  'Check In Time' will be reset to 9 am the next day.

You can test it at:

https://www.emogic.com/cgi/imok/imok.cgi

-------------------------------------

It is web page based. Any device can be used. Smart phone, PC, etc.

It was designed to be a fail safe. By having to report to a server, the server can send out the alert if you do not report in.

Program is subject to change and no assumption of reliability can be assumed.
This is a proof of concept script. Don't risk your life on it.

It also comes with a simple PERL Module, AuthorizeMe, that takes care of the account registration, password management, tokens, etc.
It also has methods you can use to easily save and retrieve database information (hash, array or scalars) in a text flat file format.

The idea for this program came to me after a relative had passed away and was not found for 7 days.

Possible to do list:

-alert to text

-alert to social media
