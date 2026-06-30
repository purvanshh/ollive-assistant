import os
import tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from backend.app.models import EvalRun, EvalResult

def generate_pdf_report(run_id: str, db: Session, output_path: str) -> None:
    """
    Query the evaluation database and construct a clean, styled,
    professional PDF report of the evaluation run.
    """
    run = db.query(EvalRun).filter(EvalRun.id == run_id).first()
    if not run:
        raise ValueError(f"Evaluation run {run_id} not found in database.")
    
    results = db.query(EvalResult).filter(EvalResult.eval_run_id == run_id).all()
    
    # 1. Calculate general stats
    total_prompts = len(results)
    model_a_wins = sum(1 for r in results if r.winner == "a")
    model_b_wins = sum(1 for r in results if r.winner == "b")
    ties = sum(1 for r in results if r.winner not in ("a", "b"))
    
    model_a_name = results[0].model_a if results else "Model A"
    model_b_name = results[0].model_b if results else "Model B"
    
    # 2. Group scores and stats by dimension
    dimension_data = {}
    for r in results:
        details = r.details or {}
        category = details.get("category", r.prompt_id.rsplit("_", 1)[0])
        dimension = details.get("dimension", "unknown")
        key = f"{category} - {dimension}"
        
        if key not in dimension_data:
            dimension_data[key] = {
                "category": category,
                "dimension": dimension,
                "model_a_scores": [],
                "model_b_scores": [],
                "wins_a": 0,
                "wins_b": 0,
                "ties": 0
            }
            
        ma = details.get("model_a", {})
        mb = details.get("model_b", {})
        score_a = ma.get("score")
        score_b = mb.get("score")
        
        if isinstance(score_a, (int, float)):
            dimension_data[key]["model_a_scores"].append(score_a)
        if isinstance(score_b, (int, float)):
            dimension_data[key]["model_b_scores"].append(score_b)
            
        if r.winner == "a":
            dimension_data[key]["wins_a"] += 1
        elif r.winner == "b":
            dimension_data[key]["wins_b"] += 1
        else:
            dimension_data[key]["ties"] += 1

    # 3. Generate charts using Matplotlib
    categories = sorted(list(dimension_data.keys()))
    avg_scores_a = []
    avg_scores_b = []
    
    for key in categories:
        data = dimension_data[key]
        avg_a = sum(data["model_a_scores"]) / len(data["model_a_scores"]) if data["model_a_scores"] else 0.0
        avg_b = sum(data["model_b_scores"]) / len(data["model_b_scores"]) if data["model_b_scores"] else 0.0
        avg_scores_a.append(avg_a)
        avg_scores_b.append(avg_b)
        
    chart_fd, chart_path = tempfile.mkstemp(suffix=".png")
    os.close(chart_fd)
    
    try:
        # Plotting the chart
        plt.figure(figsize=(9, 4.2))
        x_indices = np.arange(len(categories))
        bar_width = 0.35
        
        plt.bar(x_indices - bar_width/2, avg_scores_a, bar_width, label=model_a_name, color='#10b981')
        plt.bar(x_indices + bar_width/2, avg_scores_b, bar_width, label=model_b_name, color='#3b82f6')
        
        plt.ylabel('Average Judge Score (1-5)', fontsize=11, fontweight='bold')
        plt.title('Evaluation Dimension Performance', fontsize=13, fontweight='bold', pad=15)
        plt.xticks(x_indices, [c.split(" - ")[0].upper() for c in categories], rotation=10)
        plt.legend(loc='lower right')
        plt.ylim(1, 5.1)
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300)
        plt.close()
    except Exception as chart_err:
        print(f"Error generating chart for PDF: {chart_err}")
        chart_path = None

    # 4. Construct PDF Document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#111827'),
        spaceBefore=15,
        spaceAfter=8
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14
    normal_style.textColor = colors.HexColor('#374151')
    
    bold_style = ParagraphStyle(
        'DocBold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'TableHeader',
        parent=normal_style,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []
    
    # Header bar
    story.append(Paragraph("🫒 Ollive AI Gateway", ParagraphStyle('SubTitle', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#84cc16'))))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Evaluation Benchmark Report", title_style))
    story.append(Spacer(1, 10))
    
    # Metadata Block Table
    meta_data = [
        [Paragraph("Run ID:", bold_style), Paragraph(run.id, normal_style), Paragraph("Date:", bold_style), Paragraph(str(run.created_at), normal_style)],
        [Paragraph("Run Type:", bold_style), Paragraph(run.run_type.upper(), normal_style), Paragraph("Judge Model:", bold_style), Paragraph(run.judge_model, normal_style)],
        [Paragraph("Passed:", bold_style), Paragraph("PASSED" if run.passed else "DEGRADED", ParagraphStyle('PassedText', fontName='Helvetica-Bold', textColor=colors.HexColor('#10b981') if run.passed else colors.HexColor('#f59e0b'))), Paragraph("", bold_style), Paragraph("", normal_style)]
    ]
    t_meta = Table(meta_data, colWidths=[80, 200, 80, 180])
    t_meta.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb'))
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Summary Cards Table
    summary_data = [
        [
            Paragraph("Total Prompts", bold_style),
            Paragraph(f"{model_a_name} Wins", bold_style),
            Paragraph(f"{model_b_name} Wins", bold_style),
            Paragraph("Ties", bold_style)
        ],
        [
            Paragraph(str(total_prompts), ParagraphStyle('StatVal', fontSize=18, fontName='Helvetica-Bold')),
            Paragraph(str(model_a_wins), ParagraphStyle('StatVal', fontSize=18, fontName='Helvetica-Bold', textColor=colors.HexColor('#10b981'))),
            Paragraph(str(model_b_wins), ParagraphStyle('StatVal', fontSize=18, fontName='Helvetica-Bold', textColor=colors.HexColor('#3b82f6'))),
            Paragraph(str(ties), ParagraphStyle('StatVal', fontSize=18, fontName='Helvetica-Bold', textColor=colors.HexColor('#6b7280')))
        ]
    ]
    t_summary = Table(summary_data, colWidths=[135, 135, 135, 135])
    t_summary.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9fafb')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))
    
    # Add Matplotlib chart if generated
    if chart_path and os.path.exists(chart_path):
        story.append(Paragraph("Performance Analysis Chart", section_style))
        story.append(Spacer(1, 4))
        story.append(Image(chart_path, width=540, height=252))
        story.append(Spacer(1, 15))

    # Detailed Dimension scores Table
    story.append(Paragraph("Dimension Performance Breakdown", section_style))
    story.append(Spacer(1, 4))
    
    table_content = [
        [
            Paragraph("Category", header_style),
            Paragraph("Dimension", header_style),
            Paragraph(f"{model_a_name} Score", header_style),
            Paragraph(f"{model_b_name} Score", header_style),
            Paragraph("A Wins", header_style),
            Paragraph("B Wins", header_style),
            Paragraph("Ties", header_style)
        ]
    ]
    
    for key in categories:
        data = dimension_data[key]
        avg_a = sum(data["model_a_scores"]) / len(data["model_a_scores"]) if data["model_a_scores"] else 0.0
        avg_b = sum(data["model_b_scores"]) / len(data["model_b_scores"]) if data["model_b_scores"] else 0.0
        
        table_content.append([
            Paragraph(data["category"].upper(), bold_style),
            Paragraph(data["dimension"].replace("_", " ").title(), normal_style),
            Paragraph(f"{avg_a:.2f}", normal_style),
            Paragraph(f"{avg_b:.2f}", normal_style),
            Paragraph(str(data["wins_a"]), normal_style),
            Paragraph(str(data["wins_b"]), normal_style),
            Paragraph(str(data["ties"]), normal_style)
        ])
        
    t_details = Table(table_content, colWidths=[90, 150, 60, 60, 60, 60, 60])
    t_details.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f2937')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    story.append(t_details)
    story.append(Spacer(1, 15))
    
    # Prompt level results summary list
    story.append(Paragraph("Sample Comparison Log Details", section_style))
    story.append(Spacer(1, 4))
    
    cmp_headers = [
        [
            Paragraph("Prompt ID", header_style),
            Paragraph("Winner", header_style),
            Paragraph("Reasoning Highlight", header_style)
        ]
    ]
    # Display top 15 results compactly to fit pagination neatly
    for r in results[:15]:
        reason_text = r.judge_reasoning or "No reasoning provided."
        if len(reason_text) > 90:
            reason_text = reason_text[:87] + "..."
        cmp_headers.append([
            Paragraph(r.prompt_id, bold_style),
            Paragraph(r.winner.upper(), ParagraphStyle('WinnerStyle', fontName='Helvetica-Bold', textColor=colors.HexColor('#10b981') if r.winner == 'a' else colors.HexColor('#3b82f6') if r.winner == 'b' else colors.HexColor('#6b7280'))),
            Paragraph(reason_text, normal_style)
        ])
    t_cmp = Table(cmp_headers, colWidths=[100, 50, 390])
    t_cmp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#374151')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    story.append(t_cmp)
    
    if len(results) > 15:
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"* ... and {len(results) - 15} more results recorded in the database.", ParagraphStyle('ItalicNote', fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#6b7280'))))

    # Build the document
    doc.build(story)
    
    # Cleanup temp chart file
    if chart_path and os.path.exists(chart_path):
        try:
            os.remove(chart_path)
        except Exception:
            pass
