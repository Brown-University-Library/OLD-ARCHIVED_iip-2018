<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
>

<xsl:output method="xml" indent="no" encoding="UTF-8"/>

<xsl:template match="/">
  <!--<div type="simpleTranscription">-->
    <xsl:apply-templates select="/descendant::tei:div"/>
  <!--</div>-->
</xsl:template>

<!--<xsl:template match="div">
  <xsl:if test="@type='transcription'">
  	<div type="simpleTranscription">
 	 	<xsl:copy>
  			<xsl:copy-of select="@xml:lang | @target" />
		</xsl:copy>
    	<xsl:apply-templates/>
	</div>
  </xsl:if>
</xsl:template>-->

<xsl:template match="tei:div">
	<xsl:if test="@subtype='transcription'">
		<xsl:copy>
			<xsl:attribute name="type">edition</xsl:attribute>
			<xsl:attribute name="subtype">simpleTranscription</xsl:attribute>
			<xsl:copy-of select="@xml:lang | @target" />
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:if>
</xsl:template>

<xsl:template match="tei:p | tei:abbr | tei:add | tei:anchor | tei:age | tei:damage | tei:date | tei:del | tei:gap | tei:lb | tei:name | tei:num | tei:persName | tei:place | tei:placeName | tei:rs | tei:sic | tei:space | tei:supplied | tei:unclear | tei:span">
  <xsl:copy>
    <xsl:copy-of select="@*"/>
    <xsl:apply-templates/>
  </xsl:copy>
</xsl:template>

</xsl:stylesheet> 
