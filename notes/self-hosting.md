# Self-hosting

november 1, 2024

I've been a fan of self-hosting for a pretty long time. It's just very satisfying

except for when you do it wrong

## How not to self-host

When I first did self-hosting, I did it for a science project which aimed to see how different self-hostable services stack up against services provided by big tech, because e-waste bad

I was still very new to programming and hosting in general, so of course, I followed a ton of uninformed advice, but dunning-kruger at this point was at peak

For instance, with comparing Google Drive to self-hosting, I:

- setup VMWare ESXi on a spare laptop
- created an Ubuntu Server 18.04 VM (which was considered stable then)
- installed Samba FTP to it
- port-forwarded Samba traffic through the router
- installed OpenVPN to it (in hopes that it would somehow mask my server IP?)

So this here is how to self-host better

## How to self-host better

- Use *anything* but VMWare ESXi. Proxmox is a great alternative - it's open source, has most of ESXi's enterprise features for free, supports more storage types, generally more performant, etc etc.

- If you host any important login portals or remote desktops, definitely use a VPN. I've been using Tailscale for forwarding the Proxmox dashboard and `code-server` on some containers (yes, I test in production)

- For general web traffic, you probably want to use a reverse proxy so people can't find your approximate server location. I looked into using Cloudflare Argo Tunnels.. and ended up going all in with Cloudflare

I'll admit some of this stack depends on big evil monsters but either there's no other sane solution, or I'd be wasting my time to switching to something "more private" (aka less suspicion compared to X product) to "reduce my dependency"

(in the case of Cloudflare this might be true but none of what I'm doing is likely to be permanant anyways)

## Things I want to do to self-host better but forgot to do

- Just suck it up, get used to vim, and make a single SSH container to debug code in production

- Host the root site locally instead of through GitHub pages

idk the thought train is slowing now goodbye