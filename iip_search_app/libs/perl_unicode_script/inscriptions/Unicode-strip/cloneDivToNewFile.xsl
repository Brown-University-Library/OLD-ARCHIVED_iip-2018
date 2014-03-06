<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

<xsl:output method="xml" indent="no" encoding="UTF-8"/>

<xsl:template match="/">
  <!--<div type="simpleTranscription">-->
    <xsl:apply-templates select="/descendant::div"/>
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

<xsl:template match="div">
	<xsl:if test="@type='transcription'">
		<xsl:copy>
			<xsl:attribute name="type">simpleTranscription</xsl:attribute>
			<xsl:copy-of select="@xml:lang | @target" />
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:if>
</xsl:template>

<xsl:template match="p | abbr | add | anchor | age | damage | date | del | gap | lb | name | num | persName | place | placeName | rs | sic | space | supplied | unclear | span">
  <xsl:copy>
    <xsl:copy-of select="@*"/>
    <xsl:apply-templates/>
  </xsl:copy>
</xsl:template>

</xsl:stylesheet> 
