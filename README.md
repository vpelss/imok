# imok

A web based application that alerts family and friendss if you don't check in.

The idea for this program came to me after a relative had passed away and was not found for 7 days.

This program was designed for those who live alone.
It is a fail safe alarm that will alert friends or family by email if you do not report in.
Potential uses:
-For those who worry their animals or pets may suffer or die if their owner passed away or became incapacitated. 
-For those who live in a remote location.
-For someone taking a long trip alone.
-For those living alone and not in regular contact with anyone.

You can add up to three email addresses to send alerts to.
You select a start date and time. Then you select a Countdown time. Daily seems reasonable.
If you do not push the IMOK button before the Countdown time, it wil send an email message to all your addressees.
When you do push the IMOK button, it adds the Countdown time to the current Alert time.

Example: If you choose a start date of 10 Sept 2021 and a start time of 9 am and a Countdown time of one day, every time you push the IMOK button the program will set the next Alert time to 9 am the next day. 

You can test it at:
https://www.emogic.com/cgi/imok/imok.cgi

It is web page based. Any device can be used. Smart phone, PC, etc.

It was designed to be a fail safe. By having to report to a server, the server can send out the alert if you do not report in.

Program is subject to change and no assumption of reliability can be assumed.
This is a proof of concept script. Don't risk your life on it.

It also comes with a simple PERL Module, AuthorizeMe, that takes care of the account registration, password managemet, tokens, etc.
It also has methods you can use to easily save and retrieve database information (hash, array or scalars) in a text flat file format.

Possible to do list:
-alert to text
-alert to social media

