export default function ParseBrokerAnalysis(markdownText) {
  console.log("[broker_analysis RAW]", markdownText);
  // Initiales leeres Objekt
  const parsed = {
    technical: [],
    fundamental: [],
    sentiment: [],
    recommendation: "",
    justification: "",
    meta: {},
  };

  if (!markdownText) return parsed;

  // 1. Technical Analysis
  const techMatch = markdownText.match(/1\.\s+\*\*Technical Analysis:\*\*([\s\S]*?)(?=\n2\.|\n3\.|---|\n{2,}|$)/);

  if (techMatch) {
    parsed.technical = techMatch[1]
      .replace(/^- /gm, "") // Listen-Formatierung raus
      .replace(/\*\*/g, "") // Fettschrift raus
      .replace(/\n\s*-\s*/g, "\n") // Listenzeichen normalisieren
      .split("\n")
      .map((t) => t.trim())
      .filter((t) => t && !t.startsWith("*"));
  }

  // 2. Fundamental Analysis
  const fundMatch = markdownText.match(/2\.\s+\*\*Fundamental Analysis:\*\*([\s\S]*?)(?=\n3\.|\n4\.|---|\n{2,}|$)/);

  if (fundMatch) {
    parsed.fundamental = fundMatch[1]
      .replace(/^- /gm, "")
      .replace(/\*\*/g, "")
      .replace(/\n\s*-\s*/g, "\n")
      .split("\n")
      .map((t) => t.trim())
      .filter((t) => t && !t.startsWith("*"));
  }

  // Sentiment:
  const sentMatch = markdownText.match(/3\.\s+\*\*Sentiment Analysis:\*\*([\s\S]*?)(?=\n4\.|---|\n{2,}|$)/);

  if (sentMatch) {
    parsed.sentiment = sentMatch[1]
      .replace(/^- /gm, "")
      .replace(/\*\*/g, "")
      .replace(/\n\s*-\s*/g, "\n")
      .split("\n")
      .map((t) => t.trim())
      .filter((t) => t && !t.startsWith("*"));
  }

  // Final Recommendation (robust!)
  // 1. Bullet-Point-Format
  const finalRecListMatch = markdownText.match(
    /Final Recommendation:\*\*\s*\n\s*-\s*\*\*(.*?)\*\*\s*\n\s*-\s*\*\*Justification:\*\*\s*([\s\S]*?)(?:\n{2,}|-{2,}|Meta Data|$)/i
  );
  // 2. Überschrift + fette Zeile darunter (klassisch)
  const finalRecHeadingMatch = markdownText.match(
    /Final Recommendation:\*\*\s*\n\*\*(.*?)\*\*\s*\n- Justification:\s*([\s\S]*?)(?:\n{2,}|-{2,}|Meta Data|$)/i
  );
  // 3. NEU: Final Recommendation direkt mit Wert auf einer Zeile!
  const finalRecInlineMatch = markdownText.match(
    /Final Recommendation:\*\*\s*\*\*(.*?)\*\*\s*\n- Justification:\s*([\s\S]*?)(?:\n{2,}|-{2,}|Meta Data|$)/i
  );
  // 4. Fallback ganz am Ende
  const fallbackMatch = markdownText.match(
    /\*\*FINAL RECOMMENDATION: ([A-Z]+)\*\*/i
  );

  if (finalRecListMatch) {
    parsed.recommendation = finalRecListMatch[1].trim();
    parsed.justification = finalRecListMatch[2].trim();
  } else if (finalRecHeadingMatch) {
    parsed.recommendation = finalRecHeadingMatch[1].trim();
    parsed.justification = finalRecHeadingMatch[2].trim();
  } else if (finalRecInlineMatch) {
    parsed.recommendation = finalRecInlineMatch[1].trim();
    parsed.justification = finalRecInlineMatch[2].trim();
  } else if (fallbackMatch) {
    parsed.recommendation = fallbackMatch[1].trim();
    parsed.justification = "";
  }

  // Meta Data (robust!)
  const metaMatch = markdownText.match(
    /Meta Data SEC Files:\**([\s\S]*?)(?:\n{2,}|-{2,}|Final Recommendation|$)/i
  );
  if (metaMatch) {
    const metaBlock = metaMatch[1];
    // Hole einzelne Felder, auch wenn sie als "- **Form:** ..." oder "- Form: ..." dastehen!
    const accNum = metaBlock.match(/Accession Number:\s*\**\s*([A-Za-z0-9]+)/i);
    const repDate = metaBlock.match(/Report Date:\s*\**\s*([0-9-]+)/i);
    const form = metaBlock.match(/Form:\s*\**\s*([A-Za-z0-9 ()]+)/i);
    const cik = metaBlock.match(/CIK:\s*\**\s*([0-9]+)/i);

    parsed.meta = {
      accessionNumber: accNum ? accNum[1] : "",
      reportDate: repDate ? repDate[1] : "",
      form: form ? form[1] : "",
      cik: cik ? cik[1] : "",
    };
  }
  console.log("[metaBlock]", parsed.meta);

  console.log("[parsed]", parsed);
  return parsed;
}
