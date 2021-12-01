## IMOK

IMOK is a web based, fail safe, alarm that will email your family and friends if you don't check in.

Potential uses:

- For those living alone and do not have regular personal contact.
- For those who have animals or pets that may suffer or die if they pass away or became incapacitated.
- For those who live in a remote location.
- For those taking a trip alone.
- For those planning on getting kidnapped

## HELP

- Some options are accessed from the menu icon in the upper left corner.
- After registering for an account, click on 'Settings'.
- Add up to three email addresses to send alerts to. You must enter at least one.
- Modify the default alert message to suit your situation. Add contact numbers, instructions, etc...
- Select an 'Alert Date' and an 'Alert Time' that you will be able to 'Check In' by. 
- Select an 'Alert Interval'. Daily seems reasonable. 
- click 'Save' on the settings page.

- If you push the IMOK button before the 'Alert Date/Time' no alert will be sent to your email list, and a new 'Alert Date/Time' is set to the next 'Alert Interval'. 
- If you do not push the IMOK button before the 'Alert Time', an alert email will be sent to your email list every half hour until you push the IMOK button.
- If you push the IMNOTOK button an email alert is sent immediately to those in your email list. 

Example: If you choose an 'Alert Date' of 10 Sept 2021 and an 'Alert Time' of 9 am and an 'Alert Interval' of one day, every time you push the IMOK button your next 'Alert Date/Time' will be reset to 9 am the next day.

You can test it at: https://www.emogic.com/cgi/imok/imok.cgi

Made by [Emogic](https://www.emogic.com)

-------------------------------------

## Benefits

It is web page based. Any device can be used. Smart phone, PC, etc.

It was designed to be a fail safe. By having to report to a server, the server can send out the alert if you do not report in.

## Liabilty

This program is subject to change and no assumption of reliability can be assumed.
This is a proof of concept script. Don't risk your life on it.

## Module

It also comes with a simple PERL Module, AuthorizeMe, that takes care of the account registration, password management, tokens, etc.
It also has methods you can use to easily save and retrieve database information (hash, array or scalars) in a text flat file format.

The idea for this program came to me after a relative had passed away and was not found for 7 days.

## To Do

- alert to text
- alert to social media

## Notes

- issues with jquerymobile 1.4.5:
- target='_top' is required on anchors due to jquerymobile's ajax paging. If we don't do this, we get js ID conflicts and pages do not update correctly or at all with my js dom updates.
- ajax paging wreaked havoc with setInterval. even when the page with setInterval is no longer paged, setInterval still exists and is running
