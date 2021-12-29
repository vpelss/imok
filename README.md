[About this program](https://github.com/vpelss/imok/blob/main/IMOK.md#about)

You can try it at: https://www.emogic.com/cgi/imok/imok.cgi

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
- - any benefits gained from ajax paging are overshadowd by the issues caused by it IMO
