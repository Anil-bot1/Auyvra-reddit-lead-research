import datetime
import pytz
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import Lead, DailyResearchStat
from config import settings

class ReportService:
    @staticmethod
    def generate_daily_digest(db: Session, date_str: str = None) -> Dict[str, Any]:
        tz = pytz.timezone(settings.timezone)
        now = datetime.datetime.now(tz)
        if not date_str:
            date_str = now.strftime("%Y-%m-%d")

        # Query stats
        stat = db.query(DailyResearchStat).filter_by(date_str=date_str).first()
        reviewed_today = stat.reviewed_count if stat else db.query(Lead).count()
        qualified_today = stat.qualified_count if stat else db.query(Lead).filter(Lead.qualification_status == "Qualified").count()

        # Top qualified leads
        top_leads = db.query(Lead).filter(
            Lead.qualification_status == "Qualified"
        ).order_by(desc(Lead.score)).limit(5).all()

        # Industry summary
        ind_counts = db.query(Lead.industry, func.count(Lead.id)).group_by(Lead.industry).all()
        top_industries = sorted(ind_counts, key=lambda x: x[1], reverse=True)[:3]
        top_industries_str = ", ".join([f"{i[0]} ({i[1]})" for i in top_industries]) if top_industries else "None recorded"

        # Country summary
        cntry_counts = db.query(Lead.country, func.count(Lead.id)).group_by(Lead.country).all()
        top_countries = sorted(cntry_counts, key=lambda x: x[1], reverse=True)[:3]
        top_countries_str = ", ".join([f"{c[0]} ({c[1]})" for c in top_countries]) if top_countries else "None recorded"

        # Matching services
        srv_counts = db.query(Lead.matching_service, func.count(Lead.id)).group_by(Lead.matching_service).all()
        top_services = sorted(srv_counts, key=lambda x: x[1], reverse=True)[:3]
        top_services_str = ", ".join([f"{s[0]} ({s[1]})" for s in top_services]) if top_services else "None recorded"

        # HTML Email Body
        leads_html_rows = ""
        for lead in top_leads:
            leads_html_rows += f"""
            <tr style="border-bottom: 1px solid #1E293B;">
                <td style="padding: 10px; color: #F8FAFC; font-weight: 500;">
                    <a href="{lead.url}" target="_blank" style="color: #38BDF8; text-decoration: none;">{lead.title[:60]}...</a>
                    <div style="font-size: 12px; color: #94A3B8; margin-top: 4px;">{lead.stated_problem[:120]}...</div>
                </td>
                <td style="padding: 10px; color: #2DD4BF;">{lead.matching_service}</td>
                <td style="padding: 10px; color: #94A3B8;">{lead.industry} / {lead.country}</td>
                <td style="padding: 10px; font-weight: bold; color: #10B981; text-align: center;">{lead.score}/100</td>
            </tr>
            """

        if not leads_html_rows:
            leads_html_rows = '<tr><td colspan="4" style="padding: 15px; text-align: center; color: #94A3B8;">No qualified leads recorded for this period yet.</td></tr>'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0B0F19; color: #F8FAFC; margin: 0; padding: 20px; }}
                .container {{ max-width: 650px; margin: 0 auto; background-color: #111827; border: 1px solid #1E293B; border-radius: 8px; overflow: hidden; }}
                .header {{ background-color: #0F172A; padding: 24px; border-bottom: 1px solid #1E293B; }}
                .badge {{ display: inline-block; padding: 4px 10px; font-size: 12px; font-weight: 600; border-radius: 9999px; background-color: #1E293B; color: #38BDF8; }}
                .kpi-grid {{ display: flex; padding: 20px; gap: 15px; border-bottom: 1px solid #1E293B; background-color: #111827; }}
                .kpi-card {{ flex: 1; background-color: #1E293B; padding: 14px; border-radius: 6px; text-align: center; }}
                .kpi-num {{ font-size: 24px; font-weight: 700; color: #38BDF8; }}
                .kpi-label {{ font-size: 11px; text-transform: uppercase; color: #94A3B8; margin-top: 4px; }}
                .section {{ padding: 20px; }}
                .section-title {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: #94A3B8; margin-bottom: 12px; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
                th {{ text-align: left; padding: 8px 10px; color: #64748B; font-weight: 600; border-bottom: 1px solid #1E293B; font-size: 11px; text-transform: uppercase; }}
                .btn {{ display: inline-block; background-color: #2563EB; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 500; font-size: 14px; margin-top: 15px; }}
                .footer {{ padding: 16px 24px; background-color: #0F172A; border-top: 1px solid #1E293B; font-size: 12px; color: #64748B; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="badge">Auyvra AI Automation Agency</span>
                    <h2 style="margin: 8px 0 0 0; color: #F8FAFC;">Daily Lead Research Digest</h2>
                    <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 13px;">Date: {date_str} (Asia/Kolkata) • Scheduled: 09:00 AM</p>
                </div>

                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-num">{reviewed_today} <span style="font-size: 14px; color: #64748B;">/ 20</span></div>
                        <div class="kpi-label">Discussions Reviewed</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-num" style="color: #10B981;">{qualified_today} <span style="font-size: 14px; color: #64748B;">/ 5</span></div>
                        <div class="kpi-label">Qualified Leads</div>
                    </div>
                </div>

                <div class="section" style="border-bottom: 1px solid #1E293B;">
                    <div class="section-title">Market Breakdown</div>
                    <p style="margin: 4px 0; font-size: 13px; color: #CBD5E1;"><strong>Top Industries:</strong> {top_industries_str}</p>
                    <p style="margin: 4px 0; font-size: 13px; color: #CBD5E1;"><strong>Top Geographies:</strong> {top_countries_str}</p>
                    <p style="margin: 4px 0; font-size: 13px; color: #CBD5E1;"><strong>Top Matching Services:</strong> {top_services_str}</p>
                </div>

                <div class="section">
                    <div class="section-title">Top Shortlisted Opportunities</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Discussion / Problem</th>
                                <th>Service Match</th>
                                <th>Category / Region</th>
                                <th style="text-align: center;">Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            {leads_html_rows}
                        </tbody>
                    </table>

                    <div style="text-align: center; margin-top: 24px;">
                        <a href="{settings.dashboard_public_url}" class="btn" style="color: #FFFFFF;">Open Auyvra Dashboard</a>
                    </div>
                </div>

                <div class="footer">
                    This automated report was generated from your dedicated Auyvra Lead Research system. All personalized replies require manual review prior to outreach.
                </div>
            </div>
        </body>
        </html>
        """

        # Plaintext version
        plain_text = (
            f"AUYVRA LEAD RESEARCH DAILY DIGEST ({date_str})\n"
            f"====================================================\n\n"
            f"Progress Summary:\n"
            f"- Discussions Reviewed: {reviewed_today} / 20 Target\n"
            f"- Qualified Prospects: {qualified_today} / 5 Target\n\n"
            f"Market Breakdown:\n"
            f"- Top Industries: {top_industries_str}\n"
            f"- Top Countries: {top_countries_str}\n"
            f"- Top Services: {top_services_str}\n\n"
            f"Top Shortlisted Leads:\n"
        )
        for lead in top_leads:
            plain_text += f"* [{lead.score}/100] {lead.title} ({lead.matching_service})\n  URL: {lead.url}\n  Problem: {lead.stated_problem[:100]}...\n\n"

        plain_text += f"\nDashboard: {settings.dashboard_public_url}\nSpreadsheet: {settings.google_sheet_name}\n"

        return {
            "date": date_str,
            "subject": f"Auyvra Lead Digest: {qualified_today} Qualified Leads ({date_str})",
            "reviewed_today": reviewed_today,
            "qualified_today": qualified_today,
            "html_content": html_content,
            "plain_text": plain_text,
            "recipient": settings.alert_email_recipient
        }

    @staticmethod
    def get_google_apps_script_code() -> str:
        """
        Returns ready-to-deploy Google Apps Script for reliable 9:00 AM Asia/Kolkata
        email scheduling directly attached to the 'Auyvra Daily Leads' Google Sheet.
        """
        return """/**
 * Auyvra Lead Research - 9:00 AM Asia/Kolkata Automated Daily Digest
 * 
 * Instructions to deploy:
 * 1. Open your 'Auyvra Daily Leads' Google Spreadsheet.
 * 2. Click Extensions > Apps Script.
 * 3. Paste this script into Code.gs.
 * 4. Replace RECIPIENT_EMAIL with your email (lingamanil55@gmail.com).
 * 5. Click Triggers (clock icon on the left) > Add Trigger:
 *    - Function: sendDailyLeadDigest
 *    - Event Source: Time-driven
 *    - Type: Day timer
 *    - Time of day: 8am to 9am or 9am to 10am (Google triggers execute within this window)
 */

var RECIPIENT_EMAIL = "lingamanil55@gmail.com";
var DASHBOARD_URL = "https://auyvra-lead-research.onrender.com"; // update with your live Render URL

function sendDailyLeadDigest() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var today = Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd");
  var sheetName = "Leads_" + today;
  var sheet = ss.getSheetByName(sheetName);
  
  var totalLeads = 0;
  var qualifiedCount = 0;
  var tableRowsHtml = "";
  
  if (sheet) {
    var data = sheet.getDataRange().getValues();
    if (data.length > 1) {
      for (var i = 1; i < data.length; i++) {
        totalLeads++;
        var row = data[i];
        var title = row[3] || "Untitled";
        var url = row[4] || "#";
        var country = row[5] || "Unknown";
        var industry = row[7] || "SMB";
        var problem = row[8] || "";
        var service = row[9] || "Automation";
        var score = row[10] || 0;
        var status = row[11] || "Awaiting Review";
        
        if (status === "Qualified" || score >= 70) {
          qualifiedCount++;
          tableRowsHtml += '<tr><td style="padding: 8px; border-bottom: 1px solid #222;">' +
            '<a href="' + url + '" style="color: #38BDF8; font-weight: bold;">' + title + '</a><br>' +
            '<span style="font-size: 11px; color: #888;">' + problem.substring(0, 100) + '...</span></td>' +
            '<td style="padding: 8px; border-bottom: 1px solid #222; color: #2DD4BF;">' + service + '</td>' +
            '<td style="padding: 8px; border-bottom: 1px solid #222; color: #888;">' + industry + ' (' + country + ')</td>' +
            '<td style="padding: 8px; border-bottom: 1px solid #222; font-weight: bold; color: #10B981; text-align: center;">' + score + '</td></tr>';
        }
      }
    }
  }
  
  if (!tableRowsHtml) {
    tableRowsHtml = '<tr><td colspan="4" style="padding: 15px; text-align: center; color: #888;">No qualified leads recorded for today yet.</td></tr>';
  }
  
  var htmlBody = '<div style="font-family: sans-serif; background-color: #0B0F19; color: #F8FAFC; padding: 20px; border-radius: 8px; max-width: 650px; margin: auto;">' +
    '<h2 style="color: #38BDF8; margin-top: 0;">Auyvra Daily Lead Research Digest</h2>' +
    '<p style="color: #94A3B8; font-size: 13px;">Date: ' + today + ' (Asia/Kolkata) | Total Reviewed: ' + totalLeads + ' | Qualified: ' + qualifiedCount + '</p>' +
    '<table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px;">' +
    '<thead><tr style="text-align: left; color: #64748B; border-bottom: 2px solid #334155;">' +
    '<th style="padding: 8px;">Lead & Problem</th><th style="padding: 8px;">Service Match</th><th style="padding: 8px;">Category</th><th style="padding: 8px; text-align: center;">Score</th></tr></thead>' +
    '<tbody>' + tableRowsHtml + '</tbody></table>' +
    '<div style="margin-top: 25px; text-align: center;">' +
    '<a href="' + DASHBOARD_URL + '" style="background: #2563EB; color: #fff; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-weight: bold;">Open Auyvra Dashboard</a>' +
    '</div></div>';
    
  MailApp.sendEmail({
    to: RECIPIENT_EMAIL,
    subject: "Auyvra Daily Leads: " + qualifiedCount + " Qualified Opportunities (" + today + ")",
    htmlBody: htmlBody
  });
}
"""
