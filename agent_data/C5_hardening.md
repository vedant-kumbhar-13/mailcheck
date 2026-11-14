# C5 — Privacy & Security Hardening
**Paste this entire prompt into Claude Code (antygravity) as your first message for this chunk.**
**Model: Claude Sonnet 4.6 Thinking**
**Prerequisite: C3 AND C4 exit gates both green.**

---

## PROMPT (copy everything below this line)

---

You are a senior security-focused Python engineer. We are building **MailCheck**. This is **Chunk 5 – Privacy & Security Hardening**: add HTTP security headers, enforce the memory guard, grow the disposable list, verify IP hashing is correct, and add formula-injection protection to the CSV export (if not already present from C3).

### What to add or verify in this chunk

#### 1. Security headers middleware — `backend/app/api/middleware.py`

```python
"""
Adds security-hardening HTTP response headers to every response.
No third-party package needed; FastAPI middleware is enough.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        # Remove server identity
        response.headers.pop("Server", None)
        return response
```

Register it in `backend/app/main.py`:

```python
from app.api.middleware import SecurityHeadersMiddleware
# Add AFTER CORSMiddleware:
app.add_middleware(SecurityHeadersMiddleware)
```

#### 2. Memory guard — `backend/app/api/middleware.py` (add to same file)

```python
import os, logging
from app.config import settings

logger = logging.getLogger(__name__)

class MemoryGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            # Only available on Linux (Render runs Linux)
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        kb = int(line.split()[1])
                        mb = kb / 1024
                        if mb > settings.memory_guard_mb:
                            logger.warning("Memory guard tripped: %.1f MB", mb)
                            from fastapi.responses import JSONResponse
                            return JSONResponse(
                                status_code=503,
                                content={"error": "Server busy", "code": "SERVER_BUSY",
                                         "detail": "Memory limit reached; try again shortly"},
                            )
        except OSError:
            pass  # /proc not available on Windows dev machine; skip
        return await call_next(request)
```

Register in `main.py`:

```python
from app.api.middleware import SecurityHeadersMiddleware, MemoryGuardMiddleware
app.add_middleware(MemoryGuardMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
```

#### 3. Extend the disposable domain list

Append these additional domains to `backend/app/core/data/disposable_domains.txt`:

```
# Additional disposable / temporary email providers
10minutemail.com
10minutemail.net
10minutemail.org
20minutemail.com
33mail.com
airmail.cc
anonymousemail.me
beefmilk.com
binkmail.com
bobmail.info
bofthew.com
brefmail.com
chacuo.net
chewiemail.com
chielo.com
clrmail.com
coieo.com
coolimpool.org
correo.blogos.net
cosmorph.com
cowaway.com
daemsteam.com
deadaddress.com
deadletter.ga
despam.it
discard.email
discardmail.com
discardmail.de
disposableaddress.com
disposeamail.com
dispostable.com
dodgeit.com
dodgit.com
donemail.ru
dontreg.com
dontsendmespam.de
drdrb.com
dump-email.info
dumpandfuck.com
dumpmail.de
dumpyemail.com
e4ward.com
einrot.com
emkei.cz
enterto.de
ephemail.net
etranquil.com
explodemail.com
fakeinbox.cf
fakeinbox.com
fakemailz.com
filzmail.com
fizmail.com
fleckens.hu
flurre.com
flyspam.com
frapmail.com
freundin.ru
fux0ringduh.com
getairmail.com
getonemail.com
ghosttexter.de
givmail.com
gowikibooks.com
gowikicampus.com
gowikicars.com
gowikifilms.com
gowikigames.com
gowikimusic.com
gowikinetwork.com
gowikitravel.com
gowikitv.com
grandmasmail.com
great-host.in
greensloth.com
h8s.org
hartbot.de
herp.in
hidemail.de
hmamail.com
hochsitze.com
hopemail.biz
hulapla.de
ieatspam.eu
ieatspam.info
imails.info
inboxbear.com
instant-mail.de
ipoo.org
irish2me.com
iwi.net
jetable.com
jetable.fr.nf
jetable.net
jetable.org
jnxjn.com
junk1.tk
junk2.tk
jnxjn.com
kasmail.com
kaspop.com
keepmymail.com
killmail.com
killmail.net
kimsdisk.com
klzlk.com
koszmail.pl
kurzepost.de
letthemeatspam.com
lhsdv.com
libox.fr
lifebyfood.com
link2mail.net
litedrop.com
lol.ovpn.to
lolfreak.net
lookugly.com
lortemail.dk
losemymail.com
luggage.site
lukop.dk
m4ilweb.info
maboard.com
mail-filter.com
mail-temporaire.com
mail-temporaire.fr
mail.mezimages.net
mail1a.de
mail2rss.org
mail333.com
mailblade.net
mailblocks.com
mailbucket.org
mailcat.biz
mailcatch.com
mailexpire.com
mailfreeonline.com
mailguard.me
mailimate.com
mailincubator.com
mailismagic.com
mailme.lv
mailme24.com
mailmetrash.com
mailmoat.com
mailms.com
mailnesia.com
mailnull.com
mailpick.biz
mailproxsy.com
mailqur.com
mailrobot.com
mailscrap.com
mailshell.com
mailsiphon.com
mailslite.com
mailtemporaire.com
mailtemporaire.fr
mailtome.de
mailtrash.net
mailtv.net
mailtv.tv
mailzilla.com
manybrain.com
mbx.cc
mega.zik.dj
meltmail.com
messagebeamer.de
mezimages.net
mintemail.com
misterpinball.de
mobi.web.id
moburl.com
moncourrier.fr.nf
monemail.fr.nf
monmail.fr.nf
msa.minsmail.com
mt2009.com
mt2015.com
mymail-in.net
mymailoasis.com
mynetstore.de
myphantomemail.com
myspaceinc.com
myspaceinc.net
myspaceinc.org
myspacepimped.com
mytrashmail.com
neomailbox.com
nepwk.com
nervmich.net
nervtmich.net
netmails.com
netmails.net
netzidiot.de
netzidiot.net
newfilm.pl
neyuh.com
nicknassar.com
no-spam.ws
noblepioneer.com
nobulk.com
nomail.pw
nomail.xl.cx
nomail2me.com
nonspam.eu
nonspammer.de
noref.in
norply.com
nospamfor.us
nospammail.net
nospamthanks.info
notmailinator.com
nowmymail.net
nurfuerspam.de
nus.edu.sg
nwldx.com
objectmail.com
odaymail.com
one-time.email
oneoffemail.com
onewaymail.com
online.ms
onqin.com
opentrash.com
orangatango.com
ordinaryamerican.net
orpox.com
owlpic.com
p71ce1m.com
pancakemail.com
paplease.com
pcusers.otherinbox.com
pepbot.com
pimpedupmyspace.com
pinemail.net
plexolan.de
pmp.today
pm.me.lt
poczta.onet.pl
politikerclub.de
poofy.org
pookmail.com
postacı.com
postapex.com
postfach.de
postfach2go.de
privacy.net
proxymail.eu
prtnx.com
prtz.eu
punkass.com
putthisinyourspamdatabase.com
qq.com.junk.ripe.net
quickinbox.com
quipquip.com
r4nd0m.de
raakim.com
raxtest.com
rcpt.at
re-gister.com
reallymymail.com
receiveme.com
recursor.net
recyclemail.dk
regbypass.com
regbypass.comsafe-mail.net
rejectmail.com
rklips.com
rmqkr.net
robloxquest.com
rootfest.net
royaldoodles.com
rppkn.com
rstarmail.com
rtotnet.pw
safetypost.de
sandelf.de
sandwhichvideo.com
sanstr.com
sast.ro
saynotospams.com
scatmail.com
schafmail.de
schrott-email.de
secretemail.de
secure-mail.biz
selfdestructingmail.com
sendspamhere.com
senseless-entertainment.com
seven6s.com
sfamo.com
sfilter.de
shadowsite.net
shahweb.net
shanmail.se
sharklasers.com
shieldemail.com
shieldedmail.com
shitmail.de
shitmail.me
shitmail.org
shitmail.tk
shiyakila.cn
shortmail.net
shozemd.com
sibmail.com
sinnlos-mail.de
slapsfromlastnight.com
slaskpost.se
slave-auctions.net
sli.gg
sloppymail.com
slushmail.com
smapfree24.com
smapfree24.de
smapfree24.eu
smapfree24.info
smapfree24.net
smapfree24.org
smashmail.de
smellfear.com
snakemail.com
sneakemail.com
sneakmail.de
snkmail.com
sofimail.com
softpls.asia
sogetthis.com
soisz.com
soodo.com
soram.cc
spam.la
spam.org.tr
spam.su
spambob.com
spambob.net
spambob.org
spambox.info
spambox.irishspringrealty.com
spambox.us
spamcannon.com
spamcannon.net
spamcero.com
spamcon.org
spamcorptastic.com
spamcowboy.com
spamcowboy.net
spamcowboy.org
spamday.com
spamex.com
spamfree.eu
spamfree24.de
spamfree24.eu
spamfree24.info
spamfree24.net
spamfree24.org
spamgourmet.com
spamgourmet.net
spamgourmet.org
spamgoes.in
spamh2d.com
spamhole.com
spamify.com
spaminator.de
spamkill.info
spaml.com
spaml.de
spammotel.com
spammy.host
spamok.com
spamot.com
spampen.com
spamserver.de
spamserver2.de
spamspot.com
spamthis.co.uk
spamtroll.net
spamwc.de
speed.1s.fr
spoofmail.de
stuffmail.de
super-auswahl.de
tagmymailbox.com
techemail.com
tempalias.com
tempe-mail.com
tempemail.biz
tempemail.com
tempemail.net
tempinbox.com
tempinbox.co.uk
tempmail.eu
tempmail.it
tempmail2.com
tempomail.fr
temporamail.com
temporarioemail.com.br
temporaryemail.net
temporaryemail.us
temporaryforwarding.com
temporaryinbox.com
temporarymailaddress.com
thankyou2010.com
thisisnotmyrealemail.com
throam.com
throwam.com
throwaway.email
throwit.tk
throwme.pw
tidni.com
tittbit.in
tmail.com
tmailinator.com
toiletmail.info
tokem.co
toomail.biz
top-mailer.net
topranklist.de
tradermail.info
trash-amil.com
trash-mail.at
trash-mail.com
trash-mail.de
trash-mail.ga
trash-mail.io
trash-mail.tk
trash2009.com
trash2010.com
trash2011.com
trashdevil.com
trashdevil.de
trashemail.de
trashmail.at
trashmail.io
trashmail.me
trashmail.net
trashmail2.com
trashmailer.com
trayna.com
trickmail.net
trillianpro.com
tryalert.com
tumhmail.com
turual.com
twoweirdtricks.com
tyldd.com
uggsrock.com
umail.net
uroid.com
usenet.al
utiket.us
uyu.it
venompen.com
veryrealemail.com
viditag.com
viewcastmedia.com
viewcastmedia.net
viewcastmedia.org
vinernet.com
viralplays.com
vmail.me
vmailing.info
vpn.st
vsimcard.com
vubby.com
walkmail.net
webemail.me
weg-werf-email.de
wegwerf-email.de
wegwerf-email.net
wegwerf-email.org
wegwerfadresse.de
wegwerfemail.de
wegwerfemail.net
wegwerfemail.org
wegwerfmail.de
wegwerfmail.net
wegwerfmail.org
wegwerfmailadresse.de
welikecookies.com
wetrho.com
whyspam.me
wilemail.com
willhackforfood.biz
willselfdestruct.com
winemaven.info
wronghead.com
wuzupmail.net
www.e4ward.com
www.mailinator.com
xagloo.com
xemaps.com
xents.com
xmaily.com
xoxy.net
xsmail.com
xzzx.net
yapped.net
yeah.net
yepmail.net
yogamaven.com
yopmail.com
yopmail.fr
yopmail.net
yopmail.pp.ua
yourlms.biz
yournightmare.com
yourspamgoesto.me
yusional.com
zehnminuten.de
zehnminutenmail.de
zippymail.info
zoemail.net
zoemail.org
zomg.info
```

#### 4. Verify IP hashing in `backend/app/api/ip.py`

The file should already exist from C2. Verify that it hashes the IP:

```python
# ip.py must NOT return raw IP; it returns the raw IP for rate-limiter use only
# The rate limiter itself hashes it via self._key(raw_ip)
# So the raw IP is never stored anywhere — only the 16-char SHA-256 prefix
```

If `ip.py` returns raw IP and the rate limiter does NOT hash it, fix the rate limiter's `_key` method to hash before storing:

```python
def _key(self, raw_ip: str) -> str:
    return hashlib.sha256(raw_ip.encode()).hexdigest()[:16]
```

#### 5. Verify CSV formula injection protection

In `backend/app/api/routes.py`, the download endpoint must already prefix any cell value that starts with `=`, `+`, `-`, `@`, tab, or carriage return with `'`. Verify or add:

```python
SAFE_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

def _safe(val: str) -> str:
    return f"'{val}" if val.startswith(SAFE_PREFIXES) else val
```

---

### Tests to create

#### `backend/tests/test_security_headers.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_security_headers_present() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in r.headers
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]

@pytest.mark.asyncio
async def test_no_server_header() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/health")
    assert "Server" not in r.headers
```

#### `backend/tests/test_ip_hashing.py`

```python
from app.services.rate_limiter import RateLimiter

def test_ip_key_is_hashed_not_raw() -> None:
    rl = RateLimiter(limit=10, window_seconds=60)
    raw = "192.168.1.100"
    rl.hit(raw)
    # The key stored must NOT equal the raw IP
    assert raw not in rl._buckets
    # It should be a hex string
    for key in rl._buckets:
        assert all(c in "0123456789abcdef" for c in key), f"Key '{key}' is not a hex hash"

def test_different_ips_have_different_keys() -> None:
    rl = RateLimiter(limit=10, window_seconds=60)
    rl.hit("1.1.1.1")
    rl.hit("2.2.2.2")
    assert len(rl._buckets) == 2

def test_same_ip_accumulates() -> None:
    rl = RateLimiter(limit=10, window_seconds=60)
    for _ in range(3):
        rl.hit("1.1.1.1")
    assert sum(len(v) for v in rl._buckets.values()) == 3
```

#### `backend/tests/test_formula_injection.py`

```python
import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.models import Job, JobStatus

@pytest.mark.asyncio
async def test_formula_prefix_in_download(monkeypatch: pytest.MonkeyPatch) -> None:
    """CSV download must prefix formula-injection characters with '."""
    from app.services.job_store import store
    job, key = Job.new(total=1)
    job.status = JobStatus.READY
    job.results = [{"address": "=HYPERLINK(malicious)", "status": "valid",
                    "is_disposable": False, "is_role": False, "domain": "x.com", "checks": {}}]
    store.put(job)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"/api/jobs/{job.id}/download", headers={"X-Job-Key": key})

    store.delete(job.id)
    text = r.text
    assert "'=HYPERLINK" in text, "Formula injection not escaped"
```

#### `backend/tests/test_disposable_list.py`

```python
from app.core.lists import is_disposable

def test_extended_list_loaded() -> None:
    assert is_disposable("10minutemail.com") is True
    assert is_disposable("yopmail.com") is True
    assert is_disposable("fakeinbox.com") is True

def test_legit_still_not_disposable() -> None:
    assert is_disposable("gmail.com") is False
    assert is_disposable("outlook.com") is False
```

---

### How to run tests

```powershell
cd P:\mail_validator\backend
pytest tests/ -v
```

**Expected:**

```
30+ passed, 0 failed
```

---

### Exit gate for C5

- [ ] All 30+ tests pass
- [ ] Browser DevTools → Network → any `/api/*` response → Headers tab: X-Content-Type-Options: nosniff present
- [ ] `is_disposable("10minutemail.com")` → True
- [ ] Download a job CSV that contains `=SOMETHING` in an address → open in Excel/Sheets → verify cell shows `'=SOMETHING`, not a formula
- [ ] Git commit: `git commit -m "C5: security headers, memory guard, extended disposable list, formula injection protection"`
