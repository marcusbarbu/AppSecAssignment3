Marcus Barbu

Application Security

Prof. Dolan-Gavitt

Assignment 2

# Design

Code is available at [https://github.com/marcusbarbu/AppSecAssignment2.git](https://github.com/marcusbarbu/AppSecAssignment2.git).

In order to create the most secure webapp possible, a number of omissions were made in the name of security and simplicity.
The web app does not use a server for logins, users are an instance of a `User` object that contains their username,
phone-number for two-factor-authentication, and a `sha256` hash of their password.

The web-app only authenticates users, as there are no boundaries against which authorization is required.  Thus, it is
sufficient to check only if a valid session exists for the current user.
A token is stored in the user's cookie, which is then hashed and combined with the hash of their nonce.
This value is checked against a dictionary of known valid states in order to determine
if a user is actually logged in or not.

Front-end javascript was avoided, as there was no need to make the site aesthetically pleasing and the required 
functionality could easily be obtained with plain HTML and HTTP requests.

# Security Mitigations
## XSS
By using `Jinja` templating, the attack surface for any XSS attack is reduced, theoretically, to 0.  There are no open
CVEs against `Jinja 2.10.3`, and there are no places in the code where HTML is crafted outside of the use of the `flask`
`render_template` method.

## CSRF
On first visiting the `/login` or `/register` pages on the webapp, a `nonce` is applied to the user's session token.
This `nonce` value is used to derive a hidden field on all forms that users can provide input into.  This field has the
name `csrf` and must be submitted along with any user data for the request to be processed.

## Session Hijacking
`Flask` signs all of its cookies, making session hijacking cryptographically difficult.

## Command Injection
The backend service of this webapp requires a file in order to run.  Words input into the app are placed in a temporary
file with a random name, which is then passed to the command `./a.out {filename} wordlist.txt`.  The filename is restricted
to ascii letters, with no special characters.  Arguments to `subprocess.check_output()` are converted into argument-list
format using `shlex.split()`, a `python3` function designed to sanitize input to calls to shell functions.

## SQLi
By not having a database, I have prevented the opportunity for an attacker to exploit SQL injection.

# Testing
Automatic testing using `pytest` was done in order to verify webapp functionality.
Manual testing with common vulnerability payloads, obtained from various sources including OWASP,
was done to test for any vulnerabilities.

# Patching Vulnerabilities
Manually testing the webapp with a number of XSS and command injection payloads showed no vulnerabilities.
In order to further protect user data, use of `md5` was discontinued and replaced with `sha256`.
This makes password cracking, in the event of a data breach, more difficult.  