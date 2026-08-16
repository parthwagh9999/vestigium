# VESTIGIUM — OSINT Tool Ecosystem Coverage Matrix

This document provides a comprehensive audit of all **46 integrated OSINT transforms and adapters** in VESTIGIUM, detailing their category, input entities, output entities, posture (Passive vs Active Authorized), installation requirements, auto-investigation support, and verification status.

---

## 1. Domain & DNS Intelligence

| Tool ID | Name | Category | Inputs | Outputs | Posture | Execution Type | Requires API Key | Binary Required | Auto-Investigation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `builtin.dns_lookup` | DNS Record Lookup | Domain & DNS | `domain`, `subdomain`, `website` | `ip_address`, `mx_record`, `nameserver`, `txt_record` | PASSIVE | Local / DNS | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.reverse_dns` | Reverse DNS (PTR) | Domain & DNS | `ip_address`, `ipv6_address` | `domain`, `subdomain` | PASSIVE | Local / DNS | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.subdomain_enum` | Subdomain Enumeration | Domain & DNS | `domain`, `website` | `subdomain` | PASSIVE | API / DNS | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.subfinder` | Subfinder Subdomain Recon | Domain & DNS | `domain`, `subdomain`, `website` | `subdomain` | PASSIVE | Binary / Fallback | No | Optional | Yes (10 layers) | **VERIFIED** |
| `builtin.assetfinder` | Assetfinder Subdomain Recon | Domain & DNS | `domain`, `subdomain`, `website` | `subdomain`, `domain` | PASSIVE | Binary / Fallback | No | Optional | Yes (10 layers) | **VERIFIED** |
| `builtin.dnsrecon` | DNSRecon Zone Recon | Domain & DNS | `domain`, `subdomain`, `website` | `ip_address`, `mx_record`, `nameserver`, `txt_record` | PASSIVE | Local / DNS | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.dns_takeover` | Subdomain Takeover Detector | Domain & DNS | `domain`, `subdomain`, `website` | `cve`, `ioc`, `domain`, `cloud_asset` | LOW_IMPACT | Local / HTTP | No | No | Manual Only | **VERIFIED** |
| `builtin.amass` | Amass Subdomain Enum | Domain & DNS | `domain`, `subdomain` | `subdomain`, `ip_address`, `asn` | PASSIVE | Binary / Fallback | No | Optional | Yes (10 layers) | **VERIFIED** |
| `builtin.rdap` | RDAP Registration Intel | Domain & DNS | `domain`, `ip_address`, `asn`, `website` | `company`, `nameserver`, `person`, `country` | PASSIVE | API / RDAP | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.whois` | WHOIS Domain Lookup | Domain & DNS | `domain`, `website` | `company`, `nameserver`, `person`, `email` | PASSIVE | Local / Socket | No | No | Yes (10 layers) | **VERIFIED** |

---

## 2. Internet Asset Discovery & Port Scanning

| Tool ID | Name | Category | Inputs | Outputs | Posture | Execution Type | Requires API Key | Binary Required | Auto-Investigation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `builtin.httpx` | HTTPX Web Service Probe | Asset Discovery | `domain`, `subdomain`, `ip_address`, `website` | `website`, `server`, `url` | LOW_IMPACT | API / HTTP | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.shodan_internetdb` | Shodan InternetDB | Asset Discovery | `ip_address` | `server`, `cve`, `service` | PASSIVE | API | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.reverse_ip` | Reverse IP Lookup | Asset Discovery | `ip_address` | `domain`, `website` | PASSIVE | API | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.nmap` | Nmap Port & Service Scanner | Asset Discovery | `ip_address`, `domain`, `server` | `server`, `service`, `cve` | ACTIVE_AUTH | Binary (CLI) | No | Yes | Manual Auth | **VERIFIED** |

---

## 3. Website & Web Technology Intelligence

| Tool ID | Name | Category | Inputs | Outputs | Posture | Execution Type | Requires API Key | Binary Required | Auto-Investigation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `builtin.whatweb` | WhatWeb Fingerprinter | Web Technology | `domain`, `website`, `url`, `subdomain` | `company`, `service`, `cve` | LOW_IMPACT | Binary / Regex | No | Optional | Yes (10 layers) | **VERIFIED** |
| `builtin.wafw00f` | Wafw00f WAF Detector | Web Technology | `domain`, `website`, `url`, `subdomain` | `company`, `service`, `ioc` | LOW_IMPACT | Binary / Probe | No | Optional | Manual Only | **VERIFIED** |
| `builtin.web_scraper` | Web Tech Stack Scraper | Web Technology | `website`, `domain`, `url` | `company`, `service` | LOW_IMPACT | Local / HTML | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.website_metadata` | Website Metadata Analyzer | Web Technology | `website`, `domain`, `url` | `website`, `company` | PASSIVE | Local / HTML | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.tech_stack` | Technology Stack Detector | Web Technology | `website`, `domain`, `url` | `company`, `service` | PASSIVE | Local / Signatures | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.security_headers` | Security Headers Evaluator | Web Technology | `website`, `domain`, `url` | `ioc`, `service` | PASSIVE | Local / HTTP | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.website_social` | Social Media Discovery | Web Technology | `website`, `domain` | `social_profile`, `username` | PASSIVE | Local / Regex | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.contact_discovery` | Contact Info Discovery | Web Technology | `website`, `domain` | `email`, `phone` | PASSIVE | Local / Regex | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.website_crawler` | Website Recursive Crawler | Web Technology | `website`, `domain`, `url` | `url`, `file` | LOW_IMPACT | Local / Crawler | No | No | Manual Only | **VERIFIED** |

---

## 4. Web Archive & Certificate Intelligence

| Tool ID | Name | Category | Inputs | Outputs | Posture | Execution Type | Requires API Key | Binary Required | Auto-Investigation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `builtin.wayback` | Wayback Machine Archives | Web Archive | `domain`, `website`, `url` | `url`, `website` | PASSIVE | API | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.crtsh` | crt.sh Certificate Transp. | Certificate & TLS | `domain`, `subdomain`, `website` | `subdomain`, `certificate`, `company` | PASSIVE | API | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.tls_inspector` | TLS Certificate & SAN Inspector | Certificate & TLS | `domain`, `website`, `subdomain`, `ip_address` | `certificate`, `domain`, `company` | LOW_IMPACT | Local / SSL Socket | No | No | Yes (10 layers) | **VERIFIED** |

---

## 5. Email & Identity Intelligence

| Tool ID | Name | Category | Inputs | Outputs | Posture | Execution Type | Requires API Key | Binary Required | Auto-Investigation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `builtin.email_intel` | Email Security & Gravatar Intel | Email Intelligence | `email`, `domain` | `domain`, `social_profile`, `ioc`, `company` | PASSIVE | API / DNS | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.maigret` | Maigret Username Profiler | Username Intelligence | `username`, `person` | `social_profile`, `url`, `website` | PASSIVE | API / Probe | No | Optional | Yes (10 layers) | **VERIFIED** |
| `builtin.social_username` | Social Profile Search | Username Intelligence | `username` | `social_profile` | PASSIVE | API | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.sherlock` | Sherlock Username Hunter | Username Intelligence | `username` | `social_profile` | PASSIVE | Binary / Fallback | No | Optional | Yes (10 layers) | **VERIFIED** |
| `builtin.theharvester` | theHarvester Recon Engine | Email Intelligence | `domain`, `company` | `email`, `subdomain`, `ip_address` | PASSIVE | Binary / Fallback | No | Optional | Yes (10 layers) | **VERIFIED** |

---

## 6. Social, Developer & Document Intelligence

| Tool ID | Name | Category | Inputs | Outputs | Posture | Execution Type | Requires API Key | Binary Required | Auto-Investigation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `builtin.github_intel` | GitHub Developer & Repo Intel | GitHub & Code | `username`, `organization`, `company`, `person` | `repository`, `email`, `website`, `company` | PASSIVE | API | Optional (Vault) | No | Yes (10 layers) | **VERIFIED** |
| `builtin.public_profiles` | Public Profile Correlator | Social & Profile | `username`, `person` | `social_profile`, `wallet`, `website` | PASSIVE | API | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.document_intel` | Document Metadata Extractor | Document Intelligence | `file`, `pdf_file`, `word_file`, `excel_file`, `url` | `person`, `company`, `url`, `email`, `hash` | PASSIVE | Local / File | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.exiftool` | ExifTool Media Metadata | Document Intelligence | `file`, `image_file`, `url` | `person`, `gps_coordinate`, `camera` | PASSIVE | Binary / Fallback | No | Optional | Yes (10 layers) | **VERIFIED** |

---

## 7. Threat Intelligence & Malware / File Intelligence

| Tool ID | Name | Category | Inputs | Outputs | Posture | Execution Type | Requires API Key | Binary Required | Auto-Investigation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `builtin.virustotal` | VirusTotal Threat Intel | Threat Intelligence | `ip_address`, `domain`, `hash`, `url` | `ioc`, `malware`, `cve` | PASSIVE | API | Yes (Vault) | No | Yes (10 layers) | **VERIFIED** |
| `builtin.abuseipdb` | AbuseIPDB Threat Intel | Threat Intelligence | `ip_address`, `ipv6_address` | `ioc`, `company`, `country` | PASSIVE | API | Yes (Vault) | No | Yes (10 layers) | **VERIFIED** |
| `builtin.alienvault_otx` | AlienVault OTX Threat Intel | Threat Intelligence | `domain`, `ip_address`, `hash`, `url` | `ioc`, `threat_actor`, `malware`, `cve` | PASSIVE | API | Optional (Vault) | No | Yes (10 layers) | **VERIFIED** |
| `builtin.malware_bazaar` | MalwareBazaar Hash Intel | Malware Intelligence | `hash`, `file`, `ioc` | `malware`, `threat_actor`, `ioc` | PASSIVE | API | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.greynoise` | GreyNoise Scanner Intel | Threat Intelligence | `ip_address`, `ipv6_address` | `ioc`, `company`, `threat_actor` | PASSIVE | API | Optional (Vault) | No | Yes (10 layers) | **VERIFIED** |

---

## 8. Cloud, Network, Geospatial & Vulnerability Intelligence

| Tool ID | Name | Category | Inputs | Outputs | Posture | Execution Type | Requires API Key | Binary Required | Auto-Investigation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `builtin.cloud_detector` | Cloud Infrastructure Detector | Cloud & ASN | `ip_address`, `domain`, `subdomain`, `website` | `cloud_asset`, `company`, `asn` | PASSIVE | API / PTR / ASN | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.bgp_route` | BGP Route & Peering Intel | Cloud & ASN | `ip_address`, `asn`, `netblock` | `asn`, `company`, `netblock`, `country` | PASSIVE | API / BGPView | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.cve_intel` | NVD & CISA KEV Vulnerability | Vulnerabilities | `cve`, `company`, `server`, `ioc` | `cve`, `company`, `ioc` | PASSIVE | API / NIST NVD | Optional (Vault) | No | Yes (10 layers) | **VERIFIED** |
| `builtin.osm_geocoding` | OSM Nominatim Geocoder | Geospatial | `country`, `city`, `street_address`, `gps_coordinate` | `gps_coordinate`, `country`, `city` | PASSIVE | API / Nominatim | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.ip_geolocation` | IP Geolocation Lookup | Geospatial | `ip_address`, `ipv6_address` | `country`, `city`, `gps_coordinate`, `asn` | PASSIVE | API / DB | No | No | Yes (10 layers) | **VERIFIED** |
| `builtin.crypto_bitcoin` | Bitcoin Wallet Tracker | Blockchain | `wallet`, `bitcoin_wallet` | `wallet`, `transaction` | PASSIVE | API / Blockstream | No | No | Yes (10 layers) | **VERIFIED** |

---

## Summary & Compliance
- **Total Integrated Modules**: 46
- **Passive-First Auto-Investigation Modules**: 41
- **Active Scanning (Authorization Required)**: 1 (Nmap)
- **Zero-Duplicate Graph Law**: Compliant (Aggressive normalization and UUID primary key deduplication)
- **API Vault Integration**: Compliant (Encrypted at rest via `CryptoService`)
- **Graceful Degradation**: Compliant (Pure-Python fallbacks for all binary tools)
