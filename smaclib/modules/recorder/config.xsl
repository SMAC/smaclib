<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:func="http://smac.hefr.ch/publisher"
	extension-element-prefixes="func"
	version="1.0">
	
	<xsl:output
		method="xml"
		encoding="UTF-8"
		omit-xml-declaration="no"
		indent="yes"/>
	
	<xsl:param name="destination"/>
	
	<!--
		Due to limitations of the capture binary, max length
		of the reservation ID is 16 chars.
	-->
	<xsl:param name="reservationID"/>
	
	
	<xsl:template match="/">
		<CaptureConfig>
			<OutputDirectory><xsl:value-of select="$destination"/></OutputDirectory>
			<ContribID><xsl:value-of select="$reservationID"/></ContribID>
			
			<xsl:call-template name="channel">
				<xsl:with-param name="index">0</xsl:with-param>
				<xsl:with-param name="audio"><xsl:value-of select="true()"/></xsl:with-param>
				<xsl:with-param name="video"><xsl:value-of select="true()"/></xsl:with-param>
				<xsl:with-param name="caption">Speaker</xsl:with-param>
			</xsl:call-template>
			
			<xsl:call-template name="channel">
				<xsl:with-param name="index">1</xsl:with-param>
				<xsl:with-param name="video"><xsl:value-of select="true()"/></xsl:with-param>
				<xsl:with-param name="caption">Screen</xsl:with-param>
			</xsl:call-template>
			
			<xsl:call-template name="channel">
				<xsl:with-param name="index">2</xsl:with-param>
			</xsl:call-template>
			
			<xsl:call-template name="channel">
				<xsl:with-param name="index">3</xsl:with-param>
			</xsl:call-template>
			
			<!-- Are the File elements really necessary? -->
			<!--File videoID="0" audioID="0" name="mux_0_0"/>
			<File videoID="1" audioID="-1" name="video_1"/-->
		</CaptureConfig>
	</xsl:template>
	
	<xsl:template name="channel">
		<xsl:param name="index"/>
		
		<xsl:param name="audio" select="false()"/>
		<xsl:param name="video" select="false()"/>
		
		<!--
			Video encoding format, defaults to MPEG4 (valid values are
			MPEG1, MPEG2 and MPEG4).
		-->
		<xsl:param name="format" select="'MPEG4'"/>
		
		<!--
			Caption for the streams, defaults to an empty string.
		-->
		<xsl:param name="caption" select="'no-caption'"/>
		
		<!--
			The resolution of the video stream, defaults to 720x576 (valid
			values are 720x576 and 352x288).
		-->
		<xsl:param name="resolution" select="'720x576'"/>
		
		<!--
			Bitrate for the video channel, defaults to 4000 (valid values are in
			range 1-4000).
		-->
		<xsl:param name="video-bitrate" select="4000"/>
		
		<!--
			Sequencing mode for the video stream, defaults to IPONLY (valid values
			are IONLY, IPONLY, IPB and IPBDROP).
		-->
		<xsl:param name="sequence-mode" select="'IPONLY'"/>
		
		<!--
			Boolean flag indicating if the audio shall be acquired in
			stereo mode, defaults to yes.
		-->
		<xsl:param name="stereo" select="true()"/>
		
		<!--
			Sampling rate for the audio channel, defaults to 16 [kHz] (valid
			values are 8000, 11025, 16000, 22050, 32000, 44100 and 48000).
		-->
		<xsl:param name="sampling" select="16000"/>
		
		<!--
			Bitrate for the audio channel, defaults to 8 (valid values are in
			range 1-16).
		-->
		<xsl:param name="audio-bitrate" select="8"/>
		
		<Channel>
			<xsl:attribute name="id"><xsl:value-of select="$index"/></xsl:attribute>
			<xsl:attribute name="format">
				<xsl:choose>
					<xsl:when test="$format = 'MPEG1'">0</xsl:when>
					<xsl:when test="$format = 'MPEG2'">1</xsl:when>
					<xsl:otherwise>4</xsl:otherwise>
				</xsl:choose>
			</xsl:attribute>
			
			<Video>
				<xsl:attribute name="selected">
					<xsl:choose>
						<xsl:when test="$video">1</xsl:when>
						<xsl:otherwise>0</xsl:otherwise>
					</xsl:choose>
				</xsl:attribute>
				<xsl:attribute name="res">
					<xsl:choose>
						<xsl:when test="$resolution = '352x288'">0</xsl:when>
						<xsl:otherwise>1</xsl:otherwise>
					</xsl:choose>
				</xsl:attribute>
				<xsl:attribute name="kbps"><xsl:value-of select="$video-bitrate"/></xsl:attribute>
				<xsl:attribute name="frames">
					<xsl:choose>
						<xsl:when test="$sequence-mode = 'IONLY'">1</xsl:when>
						<xsl:when test="$sequence-mode = 'IPONLY'">2</xsl:when>
						<xsl:when test="$sequence-mode = 'IPB'">3</xsl:when>
						<xsl:otherwise>4</xsl:otherwise>
					</xsl:choose>
				</xsl:attribute>
				<xsl:attribute name="caption"><xsl:value-of select="$caption"/></xsl:attribute>
			</Video>
			
			<Audio>
				<xsl:attribute name="selected">
					<xsl:choose>
						<xsl:when test="$audio">1</xsl:when>
						<xsl:otherwise>0</xsl:otherwise>
					</xsl:choose>
				</xsl:attribute>
				<xsl:attribute name="stereo">
					<xsl:choose>
						<xsl:when test="$stereo">2</xsl:when>
						<xsl:otherwise>1</xsl:otherwise>
					</xsl:choose>
				</xsl:attribute>
				<xsl:attribute name="Hz"><xsl:value-of select="number($sampling)"/></xsl:attribute>
				<xsl:attribute name="bits"><xsl:value-of select="number($audio-bitrate)"/></xsl:attribute>
				<xsl:attribute name="caption"><xsl:value-of select="$caption"/></xsl:attribute>
			</Audio>
		</Channel>
	</xsl:template>
	
</xsl:stylesheet>