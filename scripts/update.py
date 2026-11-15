#!/usr/bin/env python3
"""Rebuilds README.md, INTERNATIONAL.md and data/new-grad-jobs.json from the lists SpaceJobs.Now publishes every night.

SpaceJobs.Now reads each space company's own careers site nightly and publishes its entry-level lists as
public files. This script reads those files, joins them into one list and writes the tables. Standard library only.
Run: python3 scripts/update.py
"""
import datetime as dt
import json
import os
import urllib.request

STORE = "https://v4jmgkewgmoxqrya.public.blob.vercel-storage.com/entry-level-pages"
SITE = "https://spacejobs.now"
TAG = "utm_source=github&utm_medium=new-grad-list"
INTERNSHIPS = STORE.replace("entry-level-pages", "internship-pages")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

TERMS = {"summer-2027": "Summer 2027", "spring-2027": "Spring 2027", "winter-2027": "Winter 2027", "fall-2027": "Fall 2027",
         "summer-2026": "Summer 2026", "fall-2026": "Fall 2026", "winter-2026": "Winter 2026", "spring-2028": "Spring 2028", "summer-2028": "Summer 2028"}
FIELDS = [
    ("ground-software", "Software and IT"), ("gnc-flight-software", "Flight software and GNC"),
    ("mechanical-structures", "Mechanical, structures and thermal"), ("avionics-electrical", "Avionics and electrical"),
    ("rf-communications", "RF, communications and payloads"), ("propulsion", "Propulsion"),
    ("systems-test", "Systems, integration and test"), ("launch-mission-ops", "Launch and mission operations"),
    ("manufacturing", "Manufacturing"), ("quality-safety", "Quality and mission assurance"),
    ("science-imaging", "Science, imaging and Earth data"), ("business-programs", "Business and programs"),
    ("supply-chain-facilities", "Supply chain and facilities"),
]
STATE_NAMES = {"AL": "alabama", "AZ": "arizona", "CA": "california", "CO": "colorado", "FL": "florida", "MD": "maryland",
               "NM": "new-mexico", "PA": "pennsylvania", "TX": "texas", "VA": "virginia", "WA": "washington", "MS": "mississippi",
               "OH": "ohio", "UT": "utah", "DC": "district-of-columbia", "NY": "new-york", "TN": "tennessee"}


def get(name):
    req = urllib.request.Request(f"{STORE}/{name}.json", headers={"User-Agent": "spacejobsnow-github-list"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def link(path):
    return f"{SITE}{path}{'&' if '?' in path else '?'}{TAG}"


def cell(text):
    return (text or "").replace("|", "/").replace("\n", " ").strip()


def in_us(job):
    return bool(job.get("states")) or bool(job.get("inUs")) or "United States" in (job.get("place") or "")


def term(job):
    return ", ".join(TERMS.get(f, f) for f in (job.get("facets") or []))


def posted(job):
    try:
        return dt.datetime.fromisoformat(job["postedAt"].replace("Z", "+00:00")).strftime("%b %-d")
    except Exception:
        return ""


STATE_LABEL = {"AL": "Alabama", "AZ": "Arizona", "CA": "California", "CO": "Colorado", "FL": "Florida", "MD": "Maryland", "NM": "New Mexico", "PA": "Pennsylvania", "TX": "Texas", "VA": "Virginia", "WA": "Washington", "MS": "Mississippi", "OH": "Ohio", "UT": "Utah", "DC": "District of Columbia", "NY": "New York", "TN": "Tennessee"}
PAGES_BASE = "https://spacejobsnow.github.io/New-Grad-Space-Jobs/"


def page(path, title, description, lines):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    front = ["---", f"title: \"{title}\"", f"description: \"{description}\"", "---", ""]
    with open(full, "w") as f:
        f.write("\n".join(front + lines + [""]))


def write_pages(by_field, by_state, today):
    """One page per field and per state (US entry-level roles only), so a search for entry-level propulsion jobs or new grad
    space jobs in Texas finds a list of exactly those; every row opens the role's page on SpaceJobs.Now."""
    written = []
    for slug, label in FIELDS:
        jobs = by_field.get(slug) or []
        if not jobs:
            continue
        written.append(f"fields/{slug}")
        companies = sorted({j["company"] for j in jobs}, key=lambda c: -sum(1 for j in jobs if j["company"] == c))
        title = f"Entry-level {label.lower()} jobs at space companies (new grad 2026 and 2027)"
        desc = f"{len(jobs)} open entry-level {label.lower()} roles at space companies in the US ({', '.join(companies[:4])} and more), updated daily."
        page(f"fields/{slug}.md", title, desc, [
            f"# {title}", "",
            f"**{len(jobs)} open in the United States at {len(companies)} companies, most at {', '.join(companies[:5])}. Updated {today}.**", "",
            f"Read each night from each company's own careers site by [SpaceJobs.Now]({link('/space-jobs-no-experience/' + slug)}), which shows the same list with pay, filters and the full postings. Many roles require US citizenship or US person status (export rules); each role's page says so.", "",
            "[All new grad space jobs](../README.md) · [By state](../README.md#by-state) · [Europe, Canada and Asia-Pacific](../INTERNATIONAL.md)", "",
        ] + rows(jobs))
    for code, jobs in by_state.items():
        if not jobs:
            continue
        written.append(f"states/{STATE_NAMES[code]}")
        name = STATE_LABEL[code]
        companies = sorted({j["company"] for j in jobs}, key=lambda c: -sum(1 for j in jobs if j["company"] == c))
        title = f"Entry-level space and aerospace jobs in {name} (new grad 2026 and 2027)"
        desc = f"{len(jobs)} open entry-level space jobs in {name} ({', '.join(companies[:4])} and more), updated daily."
        page(f"states/{STATE_NAMES[code]}.md", title, desc, [
            f"# {title}", "",
            f"**{len(jobs)} open at {len(companies)} companies, most at {', '.join(companies[:5])}. Updated {today}.**", "",
            f"Read each night from each company's own careers site by [SpaceJobs.Now]({link('/space-jobs-no-experience/' + STATE_NAMES[code])}), which shows the same list with pay, filters and the full postings. Many roles require US citizenship or US person status (export rules); each role's page says so.", "",
            "[All new grad space jobs](../README.md) · [By field](../README.md#by-field) · [Europe, Canada and Asia-Pacific](../INTERNATIONAL.md)", "",
        ] + rows(jobs))
    with open(os.path.join(ROOT, "data", "pages.txt"), "w") as f:
        f.write("\n".join([PAGES_BASE, PAGES_BASE + "INTERNATIONAL"] + [PAGES_BASE + w for w in written]) + "\n")


def rows(jobs):
    out = ["| Company | Role | Location | Pay | Posted |", "|---|---|---|---|---|"]
    for j in jobs:
        out.append(f"| **{cell(j['company'])}** | [{cell(j['title'])}]({link(j['path'])}) | {cell(j.get('place'))} | {cell(j.get('pay'))} | {posted(j)} |")
    return out


def main():
    index = get("index")
    names = [f"kind-{k['kind']}" for k in index["kinds"]] + [s["code"] for s in index["states"]] + [f"facet-{f['facet']}" for f in index.get("facets", [])]
    jobs = {}
    for name in names:
        for j in get(name).get("jobs") or []:
            if j.get("path") and j.get("title"):
                jobs[j["path"]] = j
    # The entry-level lists hold internships too; those have their own list, so they are left out here.
    intern_index = json.load(urllib.request.urlopen(urllib.request.Request(f"{INTERNSHIPS}/index.json", headers={"User-Agent": "spacejobsnow-github-list"}), timeout=60))
    intern_names = [f"kind-{k['kind']}" for k in intern_index["kinds"]] + [s["code"] for s in intern_index["states"]]
    for name in intern_names:
        req = urllib.request.Request(f"{INTERNSHIPS}/{name}.json", headers={"User-Agent": "spacejobsnow-github-list"})
        for j in json.load(urllib.request.urlopen(req, timeout=60)).get("jobs") or []:
            jobs.pop(j.get("path"), None)
    if len(jobs) < 100:
        raise SystemExit(f"only {len(jobs)} entry-level jobs read: keeping the last list")
    ordered = sorted(jobs.values(), key=lambda j: (j.get("postedAt") or "", j["company"]), reverse=True)
    us = [j for j in ordered if in_us(j)]
    abroad = [j for j in ordered if not in_us(j)]
    companies = len({j["employer"] for j in ordered})
    today = dt.datetime.now(dt.timezone.utc).strftime("%-d %b %Y")
    kinds = {}
    for j in ordered:
        kinds[j.get("kind")] = kinds.get(j.get("kind"), 0) + 1
    states = {s["code"]: s["jobs"] for s in index["states"]}

    head = [
        "# New Grad Space and Aerospace Jobs (2026 and 2027 graduates)",
        "",
        f"Every open entry-level job at space companies, read each night from the company's own careers site by [SpaceJobs.Now]({link('/space-jobs-no-experience')}), a free job board for the space industry. A role is listed when its posting asks for no prior experience, names new or recent graduates, or is an early-career level.",
        "",
        f"**{len(us)} open in the United States, {len(abroad)} in Europe, Canada and Asia-Pacific, at {companies} companies. Updated {today}.**",
        "",
        "A role is added when the company posts it and taken off when the company takes it down. Pay is shown only where the posting states it. Each role opens its page on SpaceJobs.Now with the full posting, who may apply and how.",
        "",
        "- United States: the table below",
        f"- [Europe, Canada and Asia-Pacific](INTERNATIONAL.md) ({len(abroad)} roles)",
        "- Internships and co-ops have their own list: [Summer2027-Space-Internships](https://github.com/spacejobsnow/Summer2027-Space-Internships)",
        "- The same list as data: [data/new-grad-jobs.json](data/new-grad-jobs.json) (CC BY 4.0)",
        "",
        "Many US roles require US citizenship or US person status (export rules); each role's page says so.",
        "",
        "## By field",
        "",
    ]
    us_by_field = {slug: [j for j in us if j.get("kind") == slug] for slug, _ in FIELDS}
    us_by_state = {code: [j for j in us if code in (j.get("states") or [])] for code in STATE_NAMES}
    head += [f"- [{label}](fields/{slug}.md) ({len(us_by_field[slug])} in the US)" for slug, label in FIELDS if us_by_field.get(slug)]
    head += ["", "## By state", ""]
    head.append(", ".join(f"[{STATE_LABEL[code]}](states/{STATE_NAMES[code]}.md) ({len(us_by_state[code])})" for code in sorted(us_by_state, key=lambda c: -len(us_by_state[c])) if us_by_state[code]))
    head += [
        "",
        "## Also useful",
        "",
        f"- [Space jobs that ask for no degree]({link('/space-jobs-without-a-degree')})",
        f"- [Space jobs open to non-US citizens]({link('/space-jobs-non-us-citizens')})",
        f"- [What space employers pay, by employer and kind of work]({link('/salaries')})",
        "",
        f"## United States ({len(us)})",
        "",
    ]
    foot = [
        "",
        "## Missing a company?",
        "",
        "Open an issue with the company's careers page and we look at adding it to the nightly read.",
        "",
        "The list is free to reuse with credit to SpaceJobs.Now (CC BY 4.0).",
        "",
    ]
    with open(os.path.join(ROOT, "README.md"), "w") as f:
        f.write("\n".join(head + rows(us) + foot))
    intl = [
        "# New grad space jobs in Europe, Canada and Asia-Pacific",
        "",
        f"{len(abroad)} open entry-level roles outside the United States, read each night from the company's own careers site by [SpaceJobs.Now]({link('/space-jobs-no-experience')}). Updated {today}.",
        "",
        "[Back to the United States list](README.md)",
        "",
    ]
    with open(os.path.join(ROOT, "INTERNATIONAL.md"), "w") as f:
        f.write("\n".join(intl + rows(abroad) + [""]))
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    write_pages(us_by_field, us_by_state, today)
    data = [{"company": j["company"], "title": j["title"], "location": j.get("place"), "in_us": in_us(j), "states": j.get("states") or [],
             "pay": j.get("pay"), "term": term(j) or None, "field": j.get("kind"), "posted": (j.get("postedAt") or "")[:10], "url": link(j["path"])} for j in ordered]
    with open(os.path.join(ROOT, "data", "new-grad-jobs.json"), "w") as f:
        json.dump({"source": "SpaceJobs.Now (https://spacejobs.now)", "license": "CC BY 4.0", "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"), "jobs": data}, f, indent=1)
    print(f"{len(us)} US, {len(abroad)} abroad, {companies} companies")


if __name__ == "__main__":
    main()
