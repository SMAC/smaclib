<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:func="http://smac.hefr.ch/publisher"
	extension-element-prefixes="func"
	version="1.0">
	
	<xsl:output
		method="xml"
		encoding="UTF-8"
		indent="yes"/>
	
	<xsl:param name="video"/>
	<xsl:param name="slides"/>
	
	<xsl:template match="/">
		<conference>
			<session>
				<talk>
					<abstract></abstract>
					<talkVideo>
						<speaker>
							<speakerVideo><xsl:value-of select="$video"/></speakerVideo>
						</speaker>
						<xsl:apply-templates select="/alignment/sequence"/>
					</talkVideo>
				</talk>
			</session>
		</conference>
	</xsl:template>
	
	<xsl:template match="/alignment/sequence">
		<slide>
			<numSlide><xsl:value-of select="@slide-num"/></numSlide>
			<time><xsl:value-of select="first-frame/@timestamp"/></time>
			<image><xsl:value-of select="func:format-string($slides, @slide-num)"/></image>
			<caption></caption>
		</slide>
	</xsl:template>
	
</xsl:stylesheet>