"""Built-in OSINT transforms initialization and comprehensive tool registry."""

# Core 20 Transforms (Preserved)
from app.transforms.builtin.dns_transform import DNSLookupTransform
from app.transforms.builtin.ip_geolocation import IPGeolocationTransform
from app.transforms.builtin.whois_transform import WHOISTransform
from app.transforms.builtin.reverse_dns import ReverseDNSTransform
from app.transforms.builtin.subdomain_enum import SubdomainEnumTransform
from app.transforms.builtin.shodan_internetdb import ShodanInternetDBTransform
from app.transforms.builtin.hackertarget_transforms import ReverseIPTransform
from app.transforms.builtin.social_username import UsernameSocialTransform
from app.transforms.builtin.web_scraper_transform import WebTechStackTransform
from app.transforms.builtin.crypto_transform import BitcoinWalletTransform
from app.transforms.builtin.website_intelligence import (
    WebsiteMetadataTransform,
    TechStackTransform,
    SecurityHeadersTransform,
    SocialMediaTransform,
    ContactDiscoveryTransform,
    WebsiteCrawlerTransform
)
from app.transforms.builtin.theharvester_adapter import TheHarvesterAdapter
from app.transforms.builtin.sherlock_adapter import SherlockAdapter
from app.transforms.builtin.amass_adapter import AmassAdapter
from app.transforms.builtin.exiftool_adapter import ExifToolAdapter

# Stage 2 High-Value Integrations
from app.transforms.builtin.subfinder_adapter import SubfinderAdapter
from app.transforms.builtin.crtsh_adapter import CrtShTransform
from app.transforms.builtin.nmap_adapter import NmapTransform
from app.transforms.builtin.virustotal_adapter import VirusTotalIPTransform
from app.transforms.builtin.wayback_adapter import WaybackMachineTransform

# Ecosystem Expansion Adapters
from app.transforms.builtin.assetfinder_adapter import AssetfinderAdapter
from app.transforms.builtin.dnsrecon_adapter import DNSReconTransform
from app.transforms.builtin.dns_takeover_adapter import DNSTakeoverTransform
from app.transforms.builtin.httpx_adapter import HttpxTransform
from app.transforms.builtin.whatweb_adapter import WhatWebTransform
from app.transforms.builtin.wafw00f_adapter import Wafw00fTransform
from app.transforms.builtin.tls_inspector_adapter import TLSInspectorTransform
from app.transforms.builtin.email_intel_adapter import EmailIntelTransform
from app.transforms.builtin.maigret_adapter import MaigretTransform
from app.transforms.builtin.github_intel_adapter import GitHubIntelTransform
from app.transforms.builtin.public_profiles_adapter import PublicProfilesTransform
from app.transforms.builtin.document_intel_adapter import DocumentIntelTransform
from app.transforms.builtin.abuseipdb_adapter import AbuseIPDBTransform
from app.transforms.builtin.alienvault_otx_adapter import AlienVaultOTXTransform
from app.transforms.builtin.malware_bazaar_adapter import MalwareBazaarTransform
from app.transforms.builtin.greynoise_adapter import GreyNoiseTransform
from app.transforms.builtin.cloud_detector_adapter import CloudDetectorTransform
from app.transforms.builtin.bgp_route_adapter import BGPRouteTransform
from app.transforms.builtin.rdap_adapter import RDAPTransform
from app.transforms.builtin.cve_intel_adapter import CVEIntelTransform
from app.transforms.builtin.osm_geocoding_adapter import OSMGeocodingTransform

# Stage 3 Remaining Top 30
from app.transforms.builtin.findomain_adapter import FindomainAdapter
from app.transforms.builtin.dns_history_adapter import DNSHistoryAdapter
from app.transforms.builtin.threatfox_adapter import ThreatFoxAdapter
from app.transforms.builtin.urlhaus_adapter import URLhausAdapter
from app.transforms.builtin.cisa_kev_adapter import CisaKevAdapter
from app.transforms.builtin.epss_adapter import EPSSAdapter

# Stage 4 Domain Discovery
from app.transforms.builtin.dnsenum_adapter import DNSEnumAdapter
from app.transforms.builtin.fierce_adapter import FierceAdapter
from app.transforms.builtin.certspotter_adapter import CertSpotterAdapter
from app.transforms.builtin.rapiddns_adapter import RapidDNSAdapter
from app.transforms.builtin.chaos_adapter import ChaosAdapter
from app.transforms.builtin.securitytrails_adapter import SecurityTrailsAdapter
from app.transforms.builtin.riskiq_adapter import RiskIQAdapter

# Stage 5 Network & IP Intelligence
from app.transforms.builtin.ripestat_adapter import RIPEstatAdapter
from app.transforms.builtin.bgpview_adapter import BGPViewAdapter
from app.transforms.builtin.bgptools_adapter import BGPToolsAdapter
from app.transforms.builtin.peeringdb_adapter import PeeringDBAdapter
from app.transforms.builtin.ipinfo_adapter import IPinfoAdapter
from app.transforms.builtin.censys_adapter import CensysAdapter
from app.transforms.builtin.netlas_adapter import NetlasAdapter
from app.transforms.builtin.zoomeye_adapter import ZoomEyeAdapter
from app.transforms.builtin.fofa_adapter import FofaAdapter
from app.transforms.builtin.criminalip_adapter import CriminalIPAdapter

# Stage 6 Web Intelligence
from app.transforms.builtin.wappalyzer_adapter import WappalyzerAdapter
from app.transforms.builtin.webanalyze_adapter import WebanalyzeAdapter
from app.transforms.builtin.builtwith_adapter import BuiltWithAdapter
from app.transforms.builtin.retirejs_adapter import RetireJSAdapter
from app.transforms.builtin.testssl_adapter import TestSSLAdapter

# Stage 7 Historical OSINT
from app.transforms.builtin.memento_adapter import MementoAdapter
from app.transforms.builtin.commoncrawl_adapter import CommonCrawlAdapter
from app.transforms.builtin.urlscan_adapter import URLScanAdapter
from app.transforms.builtin.securitytrails_history import SecurityTrailsHistoryAdapter
from app.transforms.builtin.censys_history import CensysHistoryAdapter

# Stage 8 Social Media & Identity
from app.transforms.builtin.blackbird_adapter import BlackbirdAdapter
from app.transforms.builtin.whatsmyname_adapter import WhatsMyNameAdapter
from app.transforms.builtin.holehe_adapter import HoleheAdapter
from app.transforms.builtin.ghunt_adapter import GHuntAdapter

# Stage 9 Active Vulnerability & Port Scanning
from app.transforms.builtin.masscan_adapter import MasscanAdapter
from app.transforms.builtin.naabu_adapter import NaabuAdapter
from app.transforms.builtin.rustscan_adapter import RustScanAdapter
# nmap_adapter already imported in another format, we'll re-import to match convention if needed, wait, it's named NmapTransform in the file, let's fix the import.
from app.transforms.builtin.nmap_adapter import NmapTransform
from app.transforms.builtin.nuclei_adapter import NucleiAdapter
from app.transforms.builtin.nikto_adapter import NiktoAdapter

# Stage 10 Enterprise Vulnerability Assessment
from app.transforms.builtin.zap_adapter import ZapAdapter
from app.transforms.builtin.wapiti_adapter import WapitiAdapter
from app.transforms.builtin.nessus_adapter import NessusAdapter
from app.transforms.builtin.openvas_adapter import OpenVASAdapter
from app.transforms.builtin.sslyze_adapter import SSLyzeAdapter

from app.transforms.registry import transform_registry


def register_builtin_transforms() -> None:
    """Register all standard built-in and ecosystem transforms with the global registry."""
    # 1. Core Transforms (Preserved)
    transform_registry.register(DNSLookupTransform)
    transform_registry.register(IPGeolocationTransform)
    transform_registry.register(WHOISTransform)
    transform_registry.register(ReverseDNSTransform)
    transform_registry.register(SubdomainEnumTransform)
    transform_registry.register(ShodanInternetDBTransform)
    transform_registry.register(ReverseIPTransform)
    transform_registry.register(UsernameSocialTransform)
    transform_registry.register(WebTechStackTransform)
    transform_registry.register(BitcoinWalletTransform)
    transform_registry.register(WebsiteMetadataTransform)
    transform_registry.register(TechStackTransform)
    transform_registry.register(SecurityHeadersTransform)
    transform_registry.register(SocialMediaTransform)
    transform_registry.register(ContactDiscoveryTransform)
    transform_registry.register(WebsiteCrawlerTransform)
    transform_registry.register(TheHarvesterAdapter)
    transform_registry.register(SherlockAdapter)
    transform_registry.register(AmassAdapter)
    transform_registry.register(ExifToolAdapter)
    
    # 2. Recon & Web Intelligence
    transform_registry.register(SubfinderAdapter)
    transform_registry.register(AssetfinderAdapter)
    transform_registry.register(DNSReconTransform)
    transform_registry.register(DNSTakeoverTransform)
    transform_registry.register(CrtShTransform)
    transform_registry.register(TLSInspectorTransform)
    transform_registry.register(HttpxTransform)
    transform_registry.register(WhatWebTransform)
    transform_registry.register(Wafw00fTransform)
    transform_registry.register(WaybackMachineTransform)
    
    # 3. Identity & Developer Intelligence
    transform_registry.register(EmailIntelTransform)
    transform_registry.register(MaigretTransform)
    transform_registry.register(GitHubIntelTransform)
    transform_registry.register(PublicProfilesTransform)
    transform_registry.register(DocumentIntelTransform)
    
    # 4. Threat & IOC Intelligence
    transform_registry.register(NmapTransform)
    transform_registry.register(VirusTotalIPTransform)
    transform_registry.register(AbuseIPDBTransform)
    transform_registry.register(AlienVaultOTXTransform)
    transform_registry.register(MalwareBazaarTransform)
    transform_registry.register(GreyNoiseTransform)
    
    # 5. Cloud, Network, Vulnerabilities & Geospatial
    transform_registry.register(CloudDetectorTransform)
    transform_registry.register(BGPRouteTransform)
    transform_registry.register(RDAPTransform)
    transform_registry.register(CVEIntelTransform)
    transform_registry.register(OSMGeocodingTransform)
    
    # 6. Stage 3 Additions
    transform_registry.register(FindomainAdapter)
    transform_registry.register(DNSHistoryAdapter)
    transform_registry.register(ThreatFoxAdapter)
    transform_registry.register(URLhausAdapter)
    transform_registry.register(CisaKevAdapter)
    transform_registry.register(EPSSAdapter)
    
    # 7. Stage 4 Domain Discovery Additions
    transform_registry.register(DNSEnumAdapter)
    transform_registry.register(FierceAdapter)
    transform_registry.register(CertSpotterAdapter)
    transform_registry.register(RapidDNSAdapter)
    transform_registry.register(ChaosAdapter)
    transform_registry.register(SecurityTrailsAdapter)
    transform_registry.register(RiskIQAdapter)
    
    # 8. Stage 5 Network Intelligence Additions
    transform_registry.register(RIPEstatAdapter)
    transform_registry.register(BGPViewAdapter)
    transform_registry.register(BGPToolsAdapter)
    transform_registry.register(PeeringDBAdapter)
    transform_registry.register(IPinfoAdapter)
    transform_registry.register(CensysAdapter)
    transform_registry.register(NetlasAdapter)
    transform_registry.register(ZoomEyeAdapter)
    transform_registry.register(FofaAdapter)
    transform_registry.register(CriminalIPAdapter)
    
    # 9. Stage 6 Web Intelligence Additions
    transform_registry.register(WappalyzerAdapter)
    transform_registry.register(WebanalyzeAdapter)
    transform_registry.register(BuiltWithAdapter)
    transform_registry.register(RetireJSAdapter)
    transform_registry.register(TestSSLAdapter)
    
    # 10. Stage 7 Historical OSINT Additions
    transform_registry.register(MementoAdapter)
    transform_registry.register(CommonCrawlAdapter)
    transform_registry.register(URLScanAdapter)
    transform_registry.register(SecurityTrailsHistoryAdapter)
    transform_registry.register(CensysHistoryAdapter)
    
    # 11. Stage 8 Social Media & Identity Additions
    transform_registry.register(BlackbirdAdapter)
    transform_registry.register(WhatsMyNameAdapter)
    transform_registry.register(HoleheAdapter)
    transform_registry.register(GHuntAdapter)
    
    # 12. Stage 9 Active Scanning Additions
    transform_registry.register(MasscanAdapter)
    transform_registry.register(NaabuAdapter)
    transform_registry.register(RustScanAdapter)
    transform_registry.register(NmapTransform)
    transform_registry.register(NucleiAdapter)
    transform_registry.register(NiktoAdapter)
    
    # 13. Stage 10 Enterprise Vulnerability Assessment
    transform_registry.register(ZapAdapter)
    transform_registry.register(WapitiAdapter)
    transform_registry.register(NessusAdapter)
    transform_registry.register(OpenVASAdapter)
    transform_registry.register(SSLyzeAdapter)
