import { memo } from 'react';
import { Handle, Position, type NodeProps, useStore } from '@xyflow/react';
import { useGraphStore } from '@/stores/graphStore';
import {
  Globe, Mail, Phone, User, Building2, Link, Server, Shield, Code,
  Hash, Bug, AlertTriangle, Flag, MapPin, Wallet, AtSign, Image,
  FileText, Video, Music, Share2, MessageCircle, Eye, Database,
  Cloud, Puzzle, Network, Lock,
} from 'lucide-react';

const ICON_MAP: Record<string, any> = {
  domain: Globe, subdomain: Globe, url: Link, website: Globe,
  email: Mail, phone: Phone, person: User, organization: Building2,
  company: Building2, ip_address: Server, ipv6_address: Server,
  asn: Network, netblock: Network, certificate: Lock,
  server: Database, cloud_asset: Cloud, repository: Code,
  github_user: Code, gitlab_user: Code,
  social_profile: Share2, twitter_profile: MessageCircle,
  facebook_profile: Share2, instagram_profile: Image,
  linkedin_profile: Building2, tiktok_profile: Video,
  youtube_profile: Video, reddit_profile: MessageCircle,
  telegram_profile: MessageCircle, discord_profile: MessageCircle,
  mastodon_profile: MessageCircle,
  username: AtSign, wallet: Wallet, bitcoin_wallet: Wallet,
  ethereum_wallet: Wallet,
  file: FileText, pdf_file: FileText, image_file: Image,
  video_file: Video, audio_file: Music,
  malware: Bug, hash: Hash, ioc: AlertTriangle,
  cve: Shield, threat_actor: Eye, campaign: Flag,
  street_address: MapPin, country: Flag, city: Building2,
  gps_coordinate: MapPin, custom: Puzzle,
  dns_record: Globe, mx_record: Mail, txt_record: FileText,
  spf_record: Shield, dkim_record: Lock, dmarc_record: Shield,
};

export const COLOR_MAP: Record<string, string> = {
  domain: '#3B82F6', // Blue
  subdomain: '#06B6D4', // Cyan
  ip_address: '#22C55E', ipv6_address: '#22C55E', // Green
  asn: '#EAB308', // Yellow
  certificate: '#A855F7', // Purple
  organization: '#F97316', company: '#F97316', // Orange
  person: '#EF4444', // Red
  email: '#EC4899', // Pink
  phone: '#14B8A6', // Teal
  server: '#166534', // Dark Green
  cloud_asset: '#38BDF8', // Sky Blue
  repository: '#9CA3AF', // Gray
  malware: '#991B1B', // Dark Red
  threat_actor: '#BE123C', // Crimson
  country: '#78350F', // Brown
  city: '#B45309', // Light Brown
  wallet: '#F59E0B', bitcoin_wallet: '#F59E0B', ethereum_wallet: '#F59E0B', // Gold
  file: '#64748B', pdf_file: '#64748B', txt_record: '#64748B', // Slate (Document)
  image_file: '#4F46E5', // Indigo
  video_file: '#D946EF', // Magenta
  audio_file: '#2DD4BF', // Turquoise
  // Other mapped from existing or general fallbacks
  username: '#EF4444', website: '#3B82F6', url: '#06B6D4', netblock: '#EAB308',
  social_profile: '#EC4899', twitter_profile: '#38BDF8', facebook_profile: '#3B82F6', 
  linkedin_profile: '#2563EB', instagram_profile: '#EC4899',
  hash: '#9CA3AF', ioc: '#F97316', cve: '#991B1B', campaign: '#BE123C',
  street_address: '#B45309', custom: '#6B7280',
};

function EntityNode({ id, data, selected }: NodeProps) {
  const entityType = (data.entityType as string) || 'custom';
  const IconComponent = ICON_MAP[entityType] || Puzzle;
  const color = (data.color as string) || COLOR_MAP[entityType] || '#6B7280';
  const label = (data.label as string) || 'Unknown';
  const value = (data.value as string) || '';
  const confidence = (data.confidence as number) ?? 1.0;

  const typeLabel = entityType.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());

  // Graph Store state for hovering/selection highlighting
  const { hoveredNodeId, highlightedNodeIds, selectedNodeId, selectedConnectedNodeIds } = useGraphStore();
  
  const isHighlighted = highlightedNodeIds.has(id) || selectedConnectedNodeIds.has(id);
  const hasActiveHighlight = hoveredNodeId !== null || selectedNodeId !== null;
  const isFaded = hasActiveHighlight && !isHighlighted && selectedNodeId !== id;
  const isActive = selected || isHighlighted;

  // Level-of-Detail (LOD) based on zoom level
  const zoom = useStore((s) => s.transform[2]);
  const showLabels = zoom > 0.4; // Slightly more forgiving than 0.6
  const showMetadata = zoom > 1.0;
  
  const scale = (data.scale as number) || 1;

  const isRoot = scale >= 3;

  return (
    <div style={{
      opacity: isFaded ? 0.15 : 1,
      transition: 'opacity 0.3s ease, transform 0.3s ease',
      transform: `scale(${scale})`,
      transformOrigin: 'center center',
      '--node-color': color,
    } as React.CSSProperties}>
      <Handle type="target" position={Position.Top} className="!bg-blue-500 !border-gray-900" />

      {isRoot ? (
        <div 
          className={`relative flex flex-col items-center justify-center text-center rounded-full shadow-2xl ${isActive ? 'ring-4' : ''}`}
          style={{ 
            width: '160px', 
            height: '160px', 
            border: `3px solid ${color}`, 
            background: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(8px)',
            boxShadow: `0 0 20px 2px ${color}40, inset 0 0 15px -5px ${color}40`,
            cursor: 'grab'
          }}
        >
          <div className="w-12 h-12 rounded-full flex items-center justify-center bg-slate-950 mb-1 shadow-inner" style={{ color, border: `1px solid ${color}40` }}>
             <IconComponent className="w-6 h-6" />
          </div>
          {showLabels && (
            <div className="w-full px-2">
              <p className="text-[11px] font-bold text-white truncate" title={label}>{label}</p>
              <p className="text-[9px] uppercase tracking-wider font-semibold opacity-80 mt-0.5" style={{ color }}>{typeLabel}</p>
            </div>
          )}
        </div>
      ) : (
        <div
          className={`vestigium-node ${isActive ? 'selected' : ''}`}
          style={isActive ? {
            boxShadow: `0 0 25px 2px ${color}40, inset 0 0 10px 1px ${color}30`,
            borderColor: color
          } : {}}
        >
          {/* Header with icon and type */}
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
              style={{ color }}
            >
              <IconComponent className="w-5 h-5" />
            </div>
            {showLabels && (
              <div className="min-w-0 flex-1">
                <p className="text-xs uppercase tracking-wider font-semibold opacity-80" style={{ color }}>
                  {typeLabel}
                </p>
                <p className="text-[13px] font-medium text-white truncate leading-tight mt-0.5" title={label}>
                  {label}
                </p>
              </div>
            )}
          </div>

          {/* Value */}
          {showLabels && value && value !== label && (
            <p className="text-xs truncate mt-2 font-mono" style={{ color: 'var(--color-vestigium-text-dim)' }} title={value}>
              {value}
            </p>
          )}

          {/* Confidence bar */}
          {showMetadata && confidence < 1.0 && (
            <div className="mt-2">
              <div className="flex items-center justify-between text-[10px] mb-0.5" style={{ color: 'var(--color-vestigium-text-muted)' }}>
                <span>Confidence</span>
                <span>{Math.round(confidence * 100)}%</span>
              </div>
              <div className="h-1 rounded-full overflow-hidden" style={{ background: 'var(--color-vestigium-surface)' }}>
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${confidence * 100}%`,
                    background: confidence > 0.7 ? '#10b981' : confidence > 0.4 ? '#f59e0b' : '#ef4444',
                  }}
                />
              </div>
            </div>
          )}

          {/* Pin indicator */}
          {Boolean(data.isPinned) && (
            <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full" style={{ background: color }} />
          )}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-blue-500 !border-gray-900" />
    </div>
  );
}

export default memo(EntityNode);
