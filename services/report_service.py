from typing import Dict, Any
from io import BytesIO
from django.utils import timezone
from apps.applications.models import Application
from apps.interviews.models import Interview
from apps.resumes.models import Resume
from apps.skills.models import UserSkill, Skill
from apps.jobs.models import Job, JobSkill
from apps.learning.models import LearningRoadmap

def build_career_report_data(user) -> Dict[str, Any]:
    """
    Gathers comprehensive career, application, and skill intelligence metrics for reporting.
    """
    profile = getattr(user, 'profile', None)
    applications = Application.objects.filter(user=user).select_related('job')
    interviews = Interview.objects.filter(user=user).select_related('application__job')
    resumes = Resume.objects.filter(user=user)
    primary_resume = resumes.filter(is_primary=True).first() or resumes.first()
    roadmap = LearningRoadmap.objects.filter(user=user).first()

    user_skills = [us.skill.name for us in user.user_skills.select_related('skill')]
    total_apps = applications.count()
    interviews_count = interviews.count()
    offers_count = applications.filter(status='OFFER').count()
    active_count = applications.filter(status__in=['APPLIED', 'ASSESSMENT', 'INTERVIEW']).count()

    return {
        'generated_at': timezone.now().strftime('%B %d, %Y'),
        'candidate_name': getattr(profile, 'full_name', '') or user.email.split('@')[0],
        'email': user.email,
        'target_role': getattr(profile, 'target_role', 'Full Stack Developer'),
        'college': getattr(profile, 'college', 'N/A'),
        'degree': getattr(profile, 'degree', 'N/A'),
        'profile_completion': getattr(profile, 'completion_percentage', 0),
        'metrics': {
            'total_applications': total_apps,
            'active_applications': active_count,
            'interviews': interviews_count,
            'offers': offers_count,
            'response_rate': round(((interviews_count + offers_count) / max(1, total_apps)) * 100, 1),
        },
        'skills': user_skills,
        'primary_resume': {
            'file_name': primary_resume.file_name if primary_resume else 'No resume uploaded',
            'match_score': primary_resume.match_score if primary_resume else 0.0,
            'score_breakdown': primary_resume.score_breakdown if primary_resume else {},
            'suggestions': primary_resume.improvement_suggestions if primary_resume else [],
        },
        'learning_progress': {
            'target_role': roadmap.target_role if roadmap else 'N/A',
            'progress_percentage': roadmap.progress_percentage if roadmap else 0,
            'total_tasks': roadmap.tasks.count() if roadmap else 0,
            'completed_tasks': roadmap.tasks.filter(status='COMPLETED').count() if roadmap else 0,
        },
        'recent_applications': [
            {
                'company': app.job.company,
                'title': app.job.title,
                'status': app.get_status_display(),
                'applied_date': app.applied_date.strftime('%Y-%m-%d') if app.applied_date else 'Saved'
            }
            for app in applications[:10]
        ]
    }

def generate_pdf_report(report_data: Dict[str, Any]) -> bytes:
    """
    Generates a clean PDF document using ReportLab.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # Title & Header
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1E293B')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#64748B')
    )

    story.append(Paragraph("InternTrack AI - Career Intelligence Report", title_style))
    story.append(Paragraph(f"Generated for: <b>{report_data['candidate_name']}</b> ({report_data['email']}) | {report_data['generated_at']}", subtitle_style))
    story.append(Spacer(1, 16))

    # Executive Summary Table
    m = report_data['metrics']
    summary_data = [
        ["Total Applications", "Active Pipeline", "Interviews Conducted", "Offers Received", "Resume Match Score"],
        [str(m['total_applications']), str(m['active_applications']), str(m['interviews']), str(m['offers']), f"{report_data['primary_resume']['match_score']}/100"]
    ]
    summary_table = Table(summary_data, colWidths=[108]*5)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#334155')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # Profile & Target Role
    section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#0F172A'))
    story.append(Paragraph("Candidate Profile & Target Focus", section_heading))
    story.append(Spacer(1, 6))
    profile_p = (
        f"<b>Target Role:</b> {report_data['target_role']} | "
        f"<b>Education:</b> {report_data['degree']} at {report_data['college']} | "
        f"<b>Profile Completion:</b> {report_data['profile_completion']}%"
    )
    story.append(Paragraph(profile_p, styles['Normal']))
    story.append(Spacer(1, 12))

    # Skills Section
    story.append(Paragraph("Verified Skills", section_heading))
    story.append(Spacer(1, 6))
    skills_text = ", ".join(report_data['skills']) if report_data['skills'] else "No skills explicitly recorded."
    story.append(Paragraph(skills_text, styles['Normal']))
    story.append(Spacer(1, 14))

    # Learning Progress
    lp = report_data['learning_progress']
    story.append(Paragraph("Skill Gap Learning Roadmap Progress", section_heading))
    story.append(Spacer(1, 6))
    learning_text = f"Goal: <b>{lp['target_role']}</b> — Completed {lp['completed_tasks']} of {lp['total_tasks']} tasks ({lp['progress_percentage']}% completion)."
    story.append(Paragraph(learning_text, styles['Normal']))
    story.append(Spacer(1, 14))

    # Recent Applications Table
    story.append(Paragraph("Recent Applications Pipeline", section_heading))
    story.append(Spacer(1, 6))
    app_rows = [["Company", "Role Title", "Stage", "Applied Date"]]
    for app in report_data['recent_applications'][:8]:
        app_rows.append([app['company'], app['title'], app['status'], app['applied_date']])

    if len(app_rows) > 1:
        app_table = Table(app_rows, colWidths=[130, 180, 110, 120])
        app_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284C7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(app_table)
    else:
        story.append(Paragraph("No applications tracked yet.", styles['Italic']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
