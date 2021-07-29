# imok

This idea came to me after a relative had passed away and was not found for 7 days.

This program was designed for those who live alone.
It is a fail safe alarm that will alert friends or family by email.
It is be great for people that have pets and worry what would happen to them if they passed away or were incapacitated.

You can add up to three email addresses to send alerts to.
You select a start date and time. Then you select a repeating interval. Daily seems reasonable.
If you do not push the IMOK button before interval time, it wil send an email message to all your addressees. You can modify the contents of the email.
When you do push the IMOK button, it adds the interval time to the current trigger time.

Example: If you choose a start date of 10 Sept 2021 and a start time of 9 am and a Count Down time of one day, every time you push the IMOK button will set the next Alert time to 9 am on the next day. 

You can test it at:
https://www.emogic.com/cgi/imok/imok.cgi

As it is web page based, any device can be used. Smart phone, PC, etc.

It was designed to be a fail safe. If it was designed as a stand alone app on a phone (no server, no web page), and your battery dies, no message would be sent. By having to report to a server, the server can send out the alert if you do not report in.

Program is subject to change and no assumption of reliability can be assumed.
This is a proof of concept script. Don't risk your life on it.

It also comes with a simple PERL Module, AuthorizeMe, that takes care of the account registration, password managemet, tokens, etc.
It also has methods you can use to easily save and retrieve database information (hash, array or scalars) to a text flat file.
