## Genie

Your guide to unlocking full potential of ERPNext.

### Raising a support ticket

With Genie, it's easy to raise a support ticket with screen and audio recording right from withing your system.

[Genie.webm](https://github.com/wahni-green/genie/assets/52111700/224de4b8-c7b7-40bb-9299-0e0cc63a63b0)


### How to enable ticket raising?

1. Install Genie on your site
2. Go go Genie Settings and check Enable Ticket Raising
3. Provide the base URL of helpdesk site and API Token.

   API Token can be generated against any user with Agent role on your helpdesk site. Store API token in the following format: `api_key:api_secret`. Colon(:) is required.
5. Add a new button to your Settings Dropdown in NavBar Settings.

   Item Type should be Action and Action should be `new genie.SupportTicket()`

#### License

MIT
