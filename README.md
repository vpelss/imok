# imok

IMOK is a web based, fail safe, alarm that will email family and friends if you don't check in.

This program was designed for those who live alone and do not have regular personal contact.

Potential uses:
-For those who worry their animals or pets may suffer or die if they pass away or became incapacitated.
-For those who live in a remote location.
-For those taking a long trip alone.
-For those living alone and not in regular personal contact.

How to use:

After registering for an account, click on 'Settings'.
You select a 'Start Date' and a 'Start Time' that you will be able to 'check in' by. 
Then you select a 'Countdown Time'. Daily seems reasonable. Once the 'Start Date' and 'Start Time' are set, the timer counts down to the The Co
You can add up to three email addresses to send alerts to.
If you do not push the IMOK button before the Countdown time, it will send an email message to all your addressees.
When you push the IMOK button, it adds the Countdown time to the current Alert time.

Example: If you choose a start date of 10 Sept 2021 and a start time of 9 am and a Countdown time of one day, every time you push the IMOK button the program will set the next Alert time to 9 am the next day.

You can test it at:

https://www.emogic.com/cgi/imok/imok.cgi

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
