import os
import re
from pathlib import Path
from docling.document_converter import DocumentConverter
import json
from collections import defaultdict

class CitationAnalyzer:
    def __init__(self, papers_directory):
        self.papers_directory = Path(papers_directory)
        self.converter = DocumentConverter()
        self.papers_data = {}
        self.citation_network = defaultdict(list)
        
    def extract_paper_info(self, file_path):
        """Extract text and metadata from a PDF or DOCX paper"""
        try:
            print(f"Converting {file_path.name}...")
            doc = self.converter.convert(str(file_path)).document
            markdown_text = doc.export_to_markdown()
            
            # Extract title (first heading after removing image comments)
            lines = markdown_text.split('\n')
            title = None
            for line in lines:
                if line.startswith('## ') and not line.lower().startswith('## a r t i c l e'):
                    title = line.replace('## ', '').strip()
                    break
            
            if not title:
                title = file_path.stem
            
            # Extract authors (look for author patterns after title)
            authors = []
            author_section_found = False
            for i, line in enumerate(lines):
                if title.lower() in line.lower() and len(line) > 20:
                    # Look in next few lines for authors
                    for j in range(i+1, min(i+10, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not next_line.startswith('#') and not next_line.startswith('<!--'):
                            # Check if line contains author-like patterns
                            if re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', next_line):
                                # Split by commas and clean up
                                potential_authors = [name.strip() for name in next_line.split(',')]
                                for author in potential_authors:
                                    # Clean author names (remove superscripts, affiliations)
                                    clean_author = re.sub(r'\s+[a-z]\s*,?\s*$', '', author)  # Remove trailing affiliations
                                    clean_author = re.sub(r'^\s*-?\s*[a-z]\s+', '', clean_author)  # Remove leading affiliations
                                    if len(clean_author.split()) >= 2:  # At least first and last name
                                        authors.append(clean_author.strip())
                                break
                    break
            
            # Extract references section
            references_text = ""
            in_references = False
            for line in lines:
                if line.lower().startswith('## references') or line.lower().startswith('# references'):
                    in_references = True
                    continue
                elif in_references:
                    if line.startswith('#') and not line.lower().startswith('# ref'):
                        break  # End of references
                    references_text += line + "\n"
            
            return {
                'filename': file_path.name,
                'title': title,
                'authors': authors,
                'full_text': markdown_text,
                'references_section': references_text
            }
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def extract_author_surnames(self, authors):
        """Extract surnames from author list"""
        surnames = []
        for author in authors:
            parts = author.strip().split()
            if parts:
                surnames.append(parts[-1])  # Last part is usually surname
        return surnames
    
    def find_references_in_text(self, paper_info, all_papers):
        """Find references to other papers in the collection"""
        references = []
        full_text = paper_info['full_text']
        refs_section = paper_info['references_section']
        
        for other_filename, other_paper in all_papers.items():
            if not other_paper or other_filename == paper_info['filename']:
                continue
            
            # Check for title matches in references section (more reliable)
            other_title = other_paper['title']
            if len(other_title) > 15:  # Only check substantial titles
                # Look for title words in references
                title_words = other_title.lower().split()
                if len(title_words) >= 3:  # Need at least 3 words
                    # Check if multiple title words appear together in references
                    title_pattern = r'\b' + r'\s+'.join(re.escape(word) for word in title_words[:4]) + r'\b'
                    if re.search(title_pattern, refs_section.lower()):
                        references.append(other_filename)
                        continue
            
            # Check for author citations in main text
            other_surnames = self.extract_author_surnames(other_paper['authors'])
            for surname in other_surnames:
                if len(surname) > 2:  # Only check meaningful surnames
                    # Citation patterns: "Smith et al. (2023)", "(Smith et al., 2023)", "Smith (2023)"
                    citation_patterns = [
                        rf'\b{re.escape(surname)}\s+et\s+al\.?\s*\(\d{{4}}\)',
                        rf'\({re.escape(surname)}\s+et\s+al\.?,?\s*\d{{4}}\)',
                        rf'\b{re.escape(surname)}\s*\(\d{{4}}\)',
                        rf'\({re.escape(surname)},?\s*\d{{4}}\)',
                        rf'\b{re.escape(surname)}\s+and\s+\w+\s*\(\d{{4}}\)',
                    ]
                    
                    for pattern in citation_patterns:
                        if re.search(pattern, full_text, re.IGNORECASE):
                            if other_filename not in references:
                                references.append(other_filename)
                            break
        
        return references
    
    def analyze_all_papers(self):
        """Process all PDFs and DOCX files and build citation network"""
        print("Starting citation analysis...")
        print("=" * 50)
        
        # First pass: extract all paper information from both PDF and DOCX files
        pdf_files = list(self.papers_directory.glob("*.pdf"))
        docx_files = list(self.papers_directory.glob("*.docx"))
        all_files = pdf_files + docx_files
        
        print(f"Found {len(pdf_files)} PDF files and {len(docx_files)} DOCX files")
        print(f"Total documents to process: {len(all_files)}")
        print()
        
        for file_path in all_files:
            paper_info = self.extract_paper_info(file_path)
            if paper_info:
                self.papers_data[file_path.name] = paper_info
                print(f"+ {file_path.name}")
                print(f"  Title: {paper_info['title']}")
                print(f"  Authors: {', '.join(paper_info['authors'][:3])}{'...' if len(paper_info['authors']) > 3 else ''}")
                print()
        
        print(f"\nSuccessfully processed {len(self.papers_data)} papers")
        print("Analyzing citations...")
        print("-" * 30)
        
        # Second pass: find citations
        for filename, paper_info in self.papers_data.items():
            references = self.find_references_in_text(paper_info, self.papers_data)
            self.citation_network[filename] = references
            
            if references:
                print(f"\n{filename}")
                print(f"   References {len(references)} other papers in collection:")
                for ref in references:
                    ref_title = self.papers_data[ref]['title']
                    print(f"   -> {ref}: {ref_title[:60]}{'...' if len(ref_title) > 60 else ''}")
    
    def generate_report(self):
        """Generate a comprehensive citation analysis report"""
        total_papers = len(self.papers_data)
        papers_with_internal_refs = sum(1 for refs in self.citation_network.values() if refs)
        total_internal_citations = sum(len(refs) for refs in self.citation_network.values())
        
        # Find most cited papers
        citation_counts = defaultdict(int)
        for refs in self.citation_network.values():
            for ref in refs:
                citation_counts[ref] += 1
        
        most_cited = sorted(citation_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Find papers that cite the most others
        most_citing = sorted(
            [(paper, len(refs)) for paper, refs in self.citation_network.items()],
            key=lambda x: x[1], reverse=True
        )
        
        report = f"""# Citation Analysis Report

## Summary Statistics
- **Total papers analyzed**: {total_papers}
- **Papers with internal references**: {papers_with_internal_refs} ({papers_with_internal_refs/total_papers*100:.1f}%)
- **Total internal citations found**: {total_internal_citations}
- **Average citations per paper**: {total_internal_citations / total_papers:.2f}
- **Citation density**: {total_internal_citations / (total_papers * (total_papers - 1)) * 100:.1f}% (of possible citations)

## Most Cited Papers (within collection)
"""
        for i, (paper, count) in enumerate(most_cited[:10], 1):
            if count > 0:
                title = self.papers_data[paper]['title']
                report += f"{i}. **{paper}** ({count} citations)\n   *{title}*\n\n"
        
        report += "\n## Papers with Most References (to other papers in collection)\n"
        for i, (paper, count) in enumerate(most_citing[:10], 1):
            if count > 0:
                title = self.papers_data[paper]['title']
                report += f"{i}. **{paper}** ({count} references)\n   *{title}*\n\n"
        
        report += "\n## Detailed Citation Network\n"
        for paper, refs in self.citation_network.items():
            if refs:
                paper_title = self.papers_data[paper]['title']
                report += f"\n### {paper}\n*{paper_title}*\n\n**References:**\n"
                for ref in refs:
                    ref_title = self.papers_data[ref]['title']
                    report += f"- {ref}: *{ref_title}*\n"
                report += "\n"
        
        return report
    
    def save_results(self, output_file="citation_analysis.json"):
        """Save results to JSON file"""
        results = {
            'papers_data': {k: {
                'filename': v['filename'],
                'title': v['title'], 
                'authors': v['authors']
            } for k, v in self.papers_data.items()},  # Exclude full text to reduce file size
            'citation_network': dict(self.citation_network)
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    # Analyze papers in the UCSC NLP Project folder
    analyzer = CitationAnalyzer("UCSC NLP Project - CB Literature")
    analyzer.analyze_all_papers()
    
    # Generate and save report
    report = analyzer.generate_report()
    print("\n" + "="*50)
    print("FINAL REPORT")
    print("="*50)
    print(report)
    
    with open("citation_report.md", "w") as f:
        f.write(report)
    
    analyzer.save_results()
    
    print("\nCitation analysis complete!")
    print("Report saved to: citation_report.md")
    print("Data saved to: citation_analysis.json")