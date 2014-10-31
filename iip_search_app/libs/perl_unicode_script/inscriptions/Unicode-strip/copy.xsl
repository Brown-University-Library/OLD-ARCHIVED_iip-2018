<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

<xsl:param name="filename">empty</xsl:param>

<xsl:output method="xml" version="1.0" omit-xml-declaration="no" indent="no" encoding="UTF-8"/>

<xsl:template match="@*|*|processing-instruction()|comment()">
  <xsl:copy>
    <xsl:apply-templates select="*|@*|text()|processing-instruction()|comment()" />
  </xsl:copy>
  <xsl:if test="self::div">
    <xsl:if test="@subtype='transcription'">
      <xsl:apply-templates select="document($filename)"/>
    </xsl:if>
  </xsl:if>
</xsl:template>


</xsl:stylesheet> 
