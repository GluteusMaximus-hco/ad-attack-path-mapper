# AD Attack Path Mapper

**🔗 Live demo:** https://ad-attack-path-mapper.onrender.com

_(First load may take ~50 seconds while the free server wakes up.)_

A blue team tool that visualizes how an attacker could climb from a
low-privilege account to Domain Admin inside a company's network, the
same question professional tools like BloodHound answer against a real
Active Directory domain.

![AD Attack Path Mapper dashboard](admapper.jpg)

## Features

- Interactive domain map showing users, groups, and computers as a graph
- Shortest-path attack analysis from any account to Domain Admin
- Plain-English breakdown of each hop in the attack chain
- Concrete fix recommendations for every risky permission
- Flags which accounts are exposed vs safely contained
- Distinct blueprint-style dashboard, not a generic template

## How it works

There's no real Active Directory behind this. The environment lives in
`data/ad_environment.json`, a simulated company ("Solace Logistics")
with realistic users, groups, computers, and permission relationships
between them, `MemberOf`, `AdminTo`, `GenericAll`, `GenericWrite`,
`ForceChangePassword`, `HasSession`, the same relationship types real AD
security tools track.

Pick a starting account like it's the one you just phished, and the tool
uses graph pathfinding (`networkx`) to find the shortest route from that
account to the Domain Admins group, then translates each hop into a plain
English sentence and a concrete fix, not just "here's a scary graph."

Not every account has a path. Out of the 9 non-admin accounts in this
environment, only 3 can actually reach Domain Admin, the rest are dead
ends. That's intentional and realistic, most accounts in a real domain
are perfectly safe, the interesting part is finding the few that aren't.

## Run it locally

If you'd rather run it yourself instead of using the live demo:

```bash
cd ad-attack-path-mapper
python -m venv venv
venv\Scripts\activate          # Windows (or venv\Scripts\python.exe / pip.exe directly if activation is blocked)
pip install -r requirements.txt
python app.py
```

Then open the local address shown in the terminal.

## Trying it out

- Pick **alice.reyes** or **ben.tan** (Helpdesk) or **svc_backup** from
  the dropdown and hit "Find Attack Path", you'll get a 6-hop chain
  straight to Domain Admins, with the path highlighted on the graph.
- Pick **erika.lim**, **felix.santos**, **grace.villanueva**,
  **carla.mendoza**, **dennis.uy**, or **svc_web** instead, these are
  dead ends, the tool will tell you the account looks safely contained.

## Project structure

ad-attack-path-mapper/
├── app.py Flask routes
├── graph.py pathfinding + plain-English narrative logic
├── data/
│ └── ad_environment.json the simulated company's AD structure
├── templates/
│ └── dashboard.html
└── static/
├── style.css blueprint/intelligence-map theme
└── dashboard.js graph rendering + path highlighting

## Future Improvements

- Let users upload their own AD data instead of using the built-in sample
- Support more relationship types (e.g. RDP sessions, DCSync rights)
- Export the discovered attack path as a report

## Disclaimer

This is an educational project built around a simulated Active Directory
environment. All users, groups, and machines are made up. It's meant for
learning how attack path analysis works, not for use against any real
network.

---
Built by Hanz Christer Ortiz
