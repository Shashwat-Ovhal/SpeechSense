# DNS Resolution Fix Guide

## Problem
`[Errno 11001] getaddrinfo failed` means Windows cannot find the Supabase server.

## Quick Fixes (Try in order)

### 1. Flush DNS Cache (DONE)
Already executed: `ipconfig /flushdns`

### 2. Change DNS Servers to Google DNS
**Steps:**
1. Open Control Panel → Network and Sharing Center
2. Click your active connection → Properties
3. Select "Internet Protocol Version 4 (TCP/IPv4)" → Properties
4. Select "Use the following DNS server addresses"
5. Enter:
   - Preferred DNS: `8.8.8.8`
   - Alternate DNS: `8.8.4.4`
6. Click OK and restart your connection

### 3. Check Hosts File
Run as Administrator:
```powershell
notepad C:\Windows\System32\drivers\etc\hosts
```
Make sure there's NO line blocking supabase.co

### 4. Disable IPv6 (Temporary)
Sometimes IPv6 causes DNS issues:
1. Network Connections → Right-click adapter → Properties
2. Uncheck "Internet Protocol Version 6 (TCP/IPv6)"
3. Click OK

### 5. Try Mobile Hotspot
Connect to your phone's hotspot to bypass network restrictions

### 6. Check Firewall/Antivirus
Temporarily disable to test if they're blocking Supabase

## Alternative: Use Supabase via IP (Advanced)
If DNS continues to fail, you can manually add to hosts file:
1. Find Supabase IP: `nslookup pviknccxlxjwordfqxrg.supabase.co 8.8.8.8`
2. Add to hosts file (as admin)

## Still Not Working?
This might be:
- Corporate/University network blocking Supabase
- ISP-level DNS issues
- Regional restrictions

**Workaround**: Use a VPN or deploy to a cloud environment (Streamlit Cloud, Replit, etc.)
