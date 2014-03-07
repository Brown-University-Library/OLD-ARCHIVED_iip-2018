<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:tei="http://www.tei-c.org/ns/1.0">
  <!--<xsl:include href="reverse.xsl"/>-->
  <xsl:template match="/">
    <xsl:element name="add">
      <xsl:apply-templates select="//inscript"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="//inscript">
    <xsl:element name="doc">
      <xsl:call-template name="inscription_id"/>
      <xsl:call-template name="place"/>
      <xsl:call-template name="placeMenu"/>
      <xsl:call-template name="place_found"/>
      <xsl:call-template name="notAfter"/>
      <xsl:call-template name="notBefore"/>
      <xsl:call-template name="type"/>
      <xsl:call-template name="language"/>
      <xsl:call-template name="religion"/>
      <xsl:call-template name="physical_type"/>
      <xsl:call-template name="figure"/>
      <xsl:call-template name="transcription"/>
      <xsl:call-template name="translation"/>
      <xsl:call-template name="diplomatic"/>
      <xsl:call-template name="dimensions"/>
      <xsl:call-template name="bibl"/>
      <xsl:call-template name="biblDiplomatic"/>
      <xsl:call-template name="biblTranscription"/>
      <xsl:call-template name="biblTranslation"/>
      <xsl:call-template name="short_description"/>
      <xsl:call-template name="description"/>
      <xsl:call-template name="image"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="inscription_id">
    <xsl:variable name="inscription_id" select="@id"/>
    <xsl:element name="field">
      <xsl:attribute name="name">inscription_id</xsl:attribute>
      <xsl:value-of select="$inscription_id"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="place">
    <xsl:choose>
      <xsl:when test="header/fileDesc/sourceDesc/physObj/discovery/place/@region">
        <xsl:variable name="placeRegion" select="header/fileDesc/sourceDesc/physObj/discovery/place/@region"/>
        <xsl:element name="field">
          <xsl:attribute name="name">region</xsl:attribute>
          <xsl:value-of select="$placeRegion"/>
        </xsl:element>
      </xsl:when>

      <xsl:when test="header/fileDesc/sourceDesc/physObj/originalLoc/place/@region">
        <xsl:variable name="placeRegion" select="header/fileDesc/sourceDesc/physObj/originalLoc/place/@region"/>
        <xsl:element name="field">
          <xsl:attribute name="name">region</xsl:attribute>
          <xsl:value-of select="$placeRegion"/>
        </xsl:element>
      </xsl:when>

      <xsl:when test="header/fileDesc/sourceDesc/physObj/currentLoc/place/@region">
        <xsl:variable name="placeRegion" select="header/fileDesc/sourceDesc/physObj/currentLoc/place/@region"/>
        <xsl:element name="field">
          <xsl:attribute name="name">region</xsl:attribute>
          <xsl:value-of select="$placeRegion"/>
        </xsl:element>
      </xsl:when>
      <xsl:otherwise/>
    </xsl:choose>
    <xsl:choose>

      <xsl:when test="header/fileDesc/sourceDesc/physObj/discovery/place/@city">
        <xsl:variable name="placecity" select="header/fileDesc/sourceDesc/physObj/discovery/place/@city"/>
        <xsl:element name="field">
          <xsl:attribute name="name">city</xsl:attribute>
          <xsl:value-of select="$placecity"/>
        </xsl:element>
      </xsl:when>

      <xsl:when test="header/fileDesc/sourceDesc/physObj/originalLoc/place/@city">
        <xsl:variable name="placecity" select="header/fileDesc/sourceDesc/physObj/originalLoc/place/@city"/>
        <xsl:element name="field">
          <xsl:attribute name="name">city</xsl:attribute>
          <xsl:value-of select="$placecity"/>
        </xsl:element>
      </xsl:when>

      <xsl:when test="header/fileDesc/sourceDesc/physObj/currentLoc/place/@city">
        <xsl:variable name="placecity" select="header/fileDesc/sourceDesc/physObj/currentLoc/place/@city"/>
        <xsl:element name="field">
          <xsl:attribute name="name">city</xsl:attribute>
          <xsl:value-of select="$placecity"/>
        </xsl:element>
      </xsl:when>
      <xsl:otherwise/>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="placeMenu">
    <xsl:element name="field">
      <xsl:attribute name="name">placeMenu</xsl:attribute>
      <xsl:choose>
        <xsl:when test="header/fileDesc/sourceDesc/physObj/discovery/place/@city != ''">
          <xsl:variable name="placeCity" select="header/fileDesc/sourceDesc/physObj/discovery/place/@city"/>
          <xsl:value-of select="$placeCity"/>
          <xsl:call-template name="placeMenuRegion"/>
        </xsl:when>
        <xsl:when test="header/fileDesc/sourceDesc/physObj/originalLoc/place/@city != ''">
          <xsl:variable name="placeCity" select="header/fileDesc/sourceDesc/physObj/originalLoc/place/@city"/>
          <xsl:value-of select="$placeCity"/>
          <xsl:call-template name="placeMenuRegion"/>
        </xsl:when>
        <xsl:when test="header/fileDesc/sourceDesc/physObj/currentLoc/place/@city != ''">
          <xsl:variable name="placeCity" select="header/fileDesc/sourceDesc/physObj/currentLoc/place/@city"/>
          <xsl:value-of select="$placeCity"/>
          <xsl:call-template name="placeMenuRegion"/>
        </xsl:when>
        <xsl:otherwise/>
      </xsl:choose>
      <!--<xsl:choose>
                <xsl:when test="header/fileDesc/sourceDesc/physObj/discovery/place/@region != ''">
                    <xsl:variable name="placeRegion"
                        select="header/fileDesc/sourceDesc/physObj/discovery/place/@region"/>
                        <xsl:text>  (</xsl:text>         
                        <xsl:value-of select="$placeRegion"/>
                        <xsl:text>)</xsl:text>
                </xsl:when>

                <xsl:when test="header/fileDesc/sourceDesc/physObj/originalLoc/place/@region != ''">
                    <xsl:variable name="placeRegion"
                        select="header/fileDesc/sourceDesc/physObj/originalLoc/place/@region"/>
                    	<xsl:text>  (</xsl:text>
                      	<xsl:value-of select="$placeRegion"/>
			<xsl:text>)</xsl:text>
                </xsl:when>

                <xsl:when test="header/fileDesc/sourceDesc/physObj/currentLoc/place/@region != ''">
                    <xsl:variable name="placeRegion"
                        select="header/fileDesc/sourceDesc/physObj/currentLoc/place/@region"/>
                    	<xsl:text>  (</xsl:text>
			<xsl:value-of select="$placeRegion"/>
			<xsl:text>)</xsl:text>
                </xsl:when>
                <xsl:otherwise/>
            </xsl:choose>-->
    </xsl:element>
    <xsl:choose>
      <xsl:when test="header/fileDesc/sourceDesc/physObj/discovery/place/@region != ''">
        <xsl:variable name="placeRegion" select="header/fileDesc/sourceDesc/physObj/discovery/place/@region"/>
        <xsl:element name="field">
          <xsl:attribute name="name">placeMenu</xsl:attribute>
          <xsl:value-of select="$placeRegion"/>
        </xsl:element>
      </xsl:when>
      <xsl:when test="header/fileDesc/sourceDesc/physObj/originalLoc/place/@region != ''">
        <xsl:variable name="placeRegion" select="header/fileDesc/sourceDesc/physObj/originalLoc/place/@region"/>
        <xsl:element name="field">
          <xsl:attribute name="name">placeMenu</xsl:attribute>
          <xsl:value-of select="$placeRegion"/>
        </xsl:element>
      </xsl:when>
      <xsl:when test="header/fileDesc/sourceDesc/physObj/currentLoc/place/@region != ''">
        <xsl:variable name="placeRegion" select="header/fileDesc/sourceDesc/physObj/currentLoc/place/@region"/>
        <xsl:element name="field">
          <xsl:attribute name="name">placeMenu</xsl:attribute>
          <xsl:value-of select="$placeRegion"/>
        </xsl:element>
      </xsl:when>
      <xsl:otherwise/>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="notAfter">
    <xsl:variable name="notAfter" select="header/fileDesc/sourceDesc/physObj/dateRange/@to"/>
    <xsl:element name="field">
      <xsl:attribute name="name">notAfter</xsl:attribute>
      <xsl:value-of select="$notAfter"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="notBefore">
    <xsl:variable name="notBefore" select="header/fileDesc/sourceDesc/physObj/dateRange/@from"/>
    <xsl:element name="field">
      <xsl:attribute name="name">notBefore</xsl:attribute>
      <xsl:value-of select="$notBefore"/>
    </xsl:element>
  </xsl:template>


  <xsl:template name="type">
    <xsl:variable name="type" select="header/fileDesc/sourceDesc/inscClass/@type"/>
    <xsl:element name="field">
      <xsl:attribute name="name">type</xsl:attribute>
      <xsl:value-of select="$type"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="language">
    <xsl:variable name="lang" select="header/fileDesc/sourceDesc/inscClass/@lang"/>
    <xsl:element name="field">
      <xsl:attribute name="name">language</xsl:attribute>
      <xsl:value-of select="$lang"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="religion">
    <xsl:variable name="religion" select="header/fileDesc/sourceDesc/inscClass/@religion"/>
    <xsl:element name="field">
      <xsl:attribute name="name">religion</xsl:attribute>
      <xsl:value-of select="$religion"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="physical_type">
    <xsl:variable name="p_d" select="header/fileDesc/sourceDesc/physObj/@type"/>
    <xsl:element name="field">
      <xsl:attribute name="name">physical_type</xsl:attribute>
      <xsl:value-of select="$p_d"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="figure">
    <xsl:for-each select="header/fileDesc/sourceDesc/figure">
      <xsl:variable name="desc" select="desc/normalize-space()"/>
      <xsl:variable name="loc" select="loc/normalize-space()"/>
      <xsl:if test="$desc!= ''">
        <xsl:element name="field">
          <xsl:attribute name="name">figure_desc</xsl:attribute>
          <xsl:value-of select="$desc"/>
        </xsl:element>
      </xsl:if>
      <xsl:if test="$loc != ''">
        <xsl:element name="field">
          <xsl:attribute name="name">figure</xsl:attribute>
          <xsl:value-of select="$desc"/> (<xsl:value-of select="$loc"/>)</xsl:element>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="place_found">
    <xsl:variable name="place_found" select="header/fileDesc/sourceDesc/physObj/discovery/place"/>
    <xsl:element name="field">
      <xsl:attribute name="name">place_found</xsl:attribute>
      <xsl:value-of select="$place_found"/>
    </xsl:element>
  </xsl:template>

  <!--    <xsl:template name="transcription">
        <xsl:variable name="transcription" select="text/body/div[@type='transcription']"/>
        <xsl:element name="field">
            <xsl:attribute name="name">transcription</xsl:attribute>
            <xsl:value-of select="$transcription"/>
        </xsl:element>
    </xsl:template>

    <xsl:template name="translation">
        <xsl:variable name="translation" select="text/body/div[@type='translation']"/>
        <xsl:element name="field">
            <xsl:attribute name="name">translation</xsl:attribute>
            <xsl:value-of select="$translation"/>
        </xsl:element>
    </xsl:template>

    <xsl:template name="diplomatic">
        <xsl:variable name="diplomatic" select="text/body/div[@type='diplomatic']"/>
        <xsl:element name="field">
            <xsl:attribute name="name">diplomatic</xsl:attribute>
            <xsl:value-of select="$diplomatic"/>
        </xsl:element>
    </xsl:template>
-->

  <xsl:template name="dimensions">
    <xsl:element name="field">
      <xsl:attribute name="name">dimensions</xsl:attribute>
      <xsl:choose>
        <xsl:when test="normalize-space(string(header/fileDesc/sourceDesc/physObj/dimensions/measure[@type='length']))">
          <xsl:value-of select="header/fileDesc/sourceDesc/physObj/dimensions/measure[@type='length']"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>N/A</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:text>; w: </xsl:text>
      <xsl:choose>
        <xsl:when test="normalize-space(string(header/fileDesc/sourceDesc/physObj/dimensions/measure[@type='width']))">
          <xsl:value-of select="header/fileDesc/sourceDesc/physObj/dimensions/measure[@type='width']"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>N/A</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:text>; d: </xsl:text>
      <xsl:choose>
        <xsl:when test="normalize-space(string(header/fileDesc/sourceDesc/physObj/dimensions/measure[@type='depth']))">
          <xsl:value-of select="header/fileDesc/sourceDesc/physObj/dimensions/measure[@type='depth']"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>N/A</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:text>; let: </xsl:text>
      <xsl:choose>
        <xsl:when test="normalize-space(string(header/fileDesc/sourceDesc/physObj/letterHgt))">
          <xsl:value-of select="header/fileDesc/sourceDesc/physObj/letterHgt"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>N/A</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>

  <xsl:template name="bibl">
    <xsl:for-each select="header/fileDesc/sourceDesc/inscSource/bibl">
      <xsl:element name="field">
        <xsl:attribute name="name">bibl</xsl:attribute>
        <xsl:text/>
        <xsl:text>bibl=</xsl:text>
        <xsl:value-of select="@ref"/>
        <xsl:text>|nType=</xsl:text>
        <xsl:value-of select="@nType"/>
        <xsl:text>|n=</xsl:text>
        <xsl:value-of select="@n"/>
      </xsl:element>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="biblDiplomatic">
    <xsl:for-each select="header/fileDesc/sourceDesc/inscSource/bibl">
      <xsl:if test="@id = ancestor::header/following-sibling::text/body/div[@type='diplomatic']/@target">
        <xsl:element name="field">
          <xsl:attribute name="name">biblDiplomatic</xsl:attribute>
          <xsl:text>bibl=</xsl:text>
          <xsl:value-of select="@ref"/>
          <xsl:text>|nType=</xsl:text>
          <xsl:value-of select="@nType"/>
          <xsl:text>|n=</xsl:text>
          <xsl:value-of select="@n"/>
        </xsl:element>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="biblTranscription">
    <xsl:for-each select="header/fileDesc/sourceDesc/inscSource/bibl">
      <xsl:if test="@id = ancestor::header/following-sibling::text/body/div[@type='transcription']/@target">
        <xsl:element name="field">
          <xsl:attribute name="name">biblTranscription</xsl:attribute>
          <xsl:text>bibl=</xsl:text>
          <xsl:value-of select="@ref"/>
          <xsl:text>|nType=</xsl:text>
          <xsl:value-of select="@nType"/>
          <xsl:text>|n=</xsl:text>
          <xsl:value-of select="@n"/>
        </xsl:element>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="biblTranslation">
    <xsl:for-each select="header/fileDesc/sourceDesc/inscSource/bibl">
      <xsl:if test="@id = ancestor::header/following-sibling::text/body/div[@type='translation']/@target">
        <xsl:element name="field">
          <xsl:attribute name="name">biblTranslation</xsl:attribute>
          <xsl:text>bibl=</xsl:text>
          <xsl:value-of select="@ref"/>
          <xsl:text>|nType=</xsl:text>
          <xsl:value-of select="@nType"/>
          <xsl:text>|n=</xsl:text>
          <xsl:value-of select="@n"/>
        </xsl:element>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>


  <xsl:template name="short_description">
    <xsl:variable name="short_desc" select="header/fileDesc/sourceDesc/physObj/desc"/>
    <xsl:element name="field">
      <xsl:attribute name="name">short_description</xsl:attribute>
      <xsl:value-of select="$short_desc"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="description">
    <xsl:variable name="desc" select="header/fileDesc/sourceDesc/physObj/note"/>
    <xsl:element name="field">
      <xsl:attribute name="name">description</xsl:attribute>
      <xsl:value-of select="$desc"/>
    </xsl:element>
  </xsl:template>

  <!--Transcription formatting cannibalized from old search.xsl-->
  <xsl:template name="diplomatic">
    <xsl:element name="field">
      <xsl:attribute name="name">diplomatic</xsl:attribute>
      <xsl:if test="text/body/div/@type='diplomatic'">
        <xsl:choose>
          <xsl:when test="text/body/div/@xml:lang='heb'">
            <![CDATA[<span dir="rtl" class="rtl">]]>
          </xsl:when>
          <xsl:otherwise><![CDATA[<span>]]></xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
          <xsl:when test="text/body/div[@type='diplomatic']/p != ''">
            <!-- <![CDATA[<br/>]]>-->
            <xsl:apply-templates select="text/body/div[@type='diplomatic']"/>
            <!--<![CDATA[<br/>]]>-->
          </xsl:when>
          <xsl:otherwise>
            <!--<![CDATA[<br/>]]>-->
            <xsl:text>[no diplomatic]</xsl:text>
            <!--<![CDATA[<br/>]]>-->
          </xsl:otherwise>
        </xsl:choose>
        <![CDATA[</span>]]>
      </xsl:if>
    </xsl:element>
  </xsl:template>

  <xsl:template name="transcription">
    <xsl:element name="field">
      <xsl:attribute name="name">transcription</xsl:attribute>
      <xsl:if test="text/body/div/@type='transcription'">
        <xsl:choose>
          <xsl:when test="text/body/div/@xml:lang='heb'">
            <![CDATA[<span dir="rtl" class="rtl">]]>
          </xsl:when>
          <xsl:otherwise><![CDATA[<span>]]></xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
          <xsl:when test="text/body/div[@type='transcription']/p != ''">
            <!--<![CDATA[<br/>]]>-->
            <xsl:apply-templates select="text/body/div[@type='transcription']"/>
            <!--<![CDATA[<br/>]]>-->
          </xsl:when>
          <xsl:otherwise>
            <!--<![CDATA[<br/>]]>-->
            <xsl:text>[no transcription]</xsl:text>
            <!--<![CDATA[<br/>]]>-->
          </xsl:otherwise>
        </xsl:choose>
        <![CDATA[</span>]]>
      </xsl:if>
    </xsl:element>
    <xsl:element name="field">
      <xsl:attribute name="name">transcription_search</xsl:attribute>
      <xsl:choose>
        <xsl:when test="string-length(text/body/div[@type='simpleTranscription']) != 0">
          <xsl:value-of select="text/body/div[@type='simpleTranscription']"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="text/body/div[@type='transcription']"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>

  <xsl:template name="translation">
    <xsl:element name="field">
      <xsl:attribute name="name">translation</xsl:attribute>
      <xsl:if test="text/body/div/@type='translation'">
        <xsl:choose>
          <xsl:when test="text/body/div[@type='translation']/p != ''">
            <!--<![CDATA[<br/>]]>-->
            <xsl:apply-templates select="text/body/div[@type='translation']"/>
            <!--<![CDATA[<br/>]]>-->
          </xsl:when>
          <xsl:otherwise>
            <!--<![CDATA[<br/>]]>-->
            <xsl:text>[no translation]</xsl:text>
            <!--<![CDATA[<br/>]]>-->
          </xsl:otherwise>
        </xsl:choose>
      </xsl:if>
    </xsl:element>
    <xsl:element name="field">
      <xsl:attribute name="name">translation_search</xsl:attribute>
      <xsl:value-of select="text/body/div[@type='translation']"/>
    </xsl:element>

  </xsl:template>

  <xsl:template name="image">
    <xsl:if test="header/fileDesc/sourceDesc/images/image/@id">
      <xsl:for-each select="header/fileDesc/sourceDesc/images/image">
        <xsl:element name="field">
          <xsl:attribute name="name">image</xsl:attribute>
          <xsl:if test="substring(@id, 1, 2) ='i_' ">
            <xsl:value-of select="substring(@id,3)"/>
          </xsl:if>
        </xsl:element>
        <xsl:if test="imgSource/note">
          <xsl:element name="field">
            <xsl:attribute name="name">imageSource</xsl:attribute>
            <xsl:value-of select="imgSource/note"/>
          </xsl:element>
        </xsl:if>
      </xsl:for-each>
    </xsl:if>
  </xsl:template>

  <xsl:template match="note"> </xsl:template>

  <xsl:template match="lb">
    <![CDATA[<br/>]]>
  </xsl:template>

  <xsl:template match="span">
    <xsl:choose>
      <xsl:when test="text/body/div/@xml:lang='heb'">
        <![CDATA[<span dir="rtl" class="rtl">]]>
      </xsl:when>
      <xsl:otherwise><![CDATA[<span>]]></xsl:otherwise>
    </xsl:choose>
    <xsl:apply-templates/>
    <![CDATA[</span>]]>
  </xsl:template>

  <xsl:template match="unclear">
    <xsl:choose>
      <xsl:when test="* | text()">
        <![CDATA[<u>]]>
        <xsl:apply-templates/>
        <![CDATA[</u>]]>
      </xsl:when>
      <xsl:otherwise>
        <![CDATA[<u>]]>
        <![CDATA[</u>]]>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="gap">
    <xsl:choose>
      <xsl:when test="@extent = '1'">
        <xsl:text>[-]</xsl:text>
      </xsl:when>
      <xsl:when test="@extent = '2'">
        <xsl:text>[--]</xsl:text>
      </xsl:when>
      <xsl:when test="@extent = '3'">
        <xsl:text>[---]</xsl:text>
      </xsl:when>
      <xsl:when test="@extent = '4'">
        <xsl:text>[----]</xsl:text>
      </xsl:when>
      <xsl:when test="@extent = '5'">
        <xsl:text>[-----]</xsl:text>
      </xsl:when>
      <xsl:when test="@extent = '6'">
        <xsl:text>[------]</xsl:text>
      </xsl:when>
      <xsl:when test="@extent = '7'">
        <xsl:text>[-------]</xsl:text>
      </xsl:when>
      <xsl:when test="@extent = '8'">
        <xsl:text>[--------]</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>[-----]</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="add">
    <xsl:text>(</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>)</xsl:text>
  </xsl:template>

  <xsl:template match="del">
    <xsl:text>[[</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>]]</xsl:text>
  </xsl:template>

  <xsl:template match="supplied">
    <xsl:text>[</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>]</xsl:text>
  </xsl:template>
  <xsl:template name="get-figures">
    <xsl:param name="figures"/>
    <xsl:for-each select="$figures">
      <xsl:value-of select="desc"/>
      <xsl:if test="string(loc) != ''">
        <xsl:text> ( </xsl:text>
        <xsl:value-of select="loc"/>
        <xsl:if test="position()!=last()">); </xsl:if>
        <xsl:if test="position()=last()">).</xsl:if>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="placeMenuRegion">
    <xsl:choose>
      <xsl:when test="header/fileDesc/sourceDesc/physObj/discovery/place/@region != ''">
        <xsl:variable name="placeRegion" select="header/fileDesc/sourceDesc/physObj/discovery/place/@region"/>
        <xsl:text>  (</xsl:text>
        <xsl:value-of select="$placeRegion"/>
        <xsl:text>)</xsl:text>
      </xsl:when>

      <xsl:when test="header/fileDesc/sourceDesc/physObj/originalLoc/place/@region != ''">
        <xsl:variable name="placeRegion" select="header/fileDesc/sourceDesc/physObj/originalLoc/place/@region"/>
        <xsl:text>  (</xsl:text>
        <xsl:value-of select="$placeRegion"/>
        <xsl:text>)</xsl:text>
      </xsl:when>

      <xsl:when test="header/fileDesc/sourceDesc/physObj/currentLoc/place/@region != ''">
        <xsl:variable name="placeRegion" select="header/fileDesc/sourceDesc/physObj/currentLoc/place/@region"/>
        <xsl:text>  (</xsl:text>
        <xsl:value-of select="$placeRegion"/>
        <xsl:text>)</xsl:text>
      </xsl:when>
      <xsl:otherwise/>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
