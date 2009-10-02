package com.wombatinvasion.pmwikidraw;

import java.net.MalformedURLException;
import java.net.URL;

import org.jhotdraw.framework.Drawing;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2004</p>
 * @author Ciaran Jessup
 * @version 1.0
 */

/*
 *  Modified:
 *   11-Nov-2004	cj       Initial development
 */

//------------------------------------------------------------------------------
/**
 * PmWikiSource
 */
public interface PmWikiSource
{
  public static final String PARAMETER_DRAWING 					= "drawingname";
  public static final String PARAMETER_WIKIURL 					= "wikiurl";
  public static final String PARAMETER_PAGENAME 				= "pagename";
  public static final String PARAMETER_DRAWINGLOADPATH 			= "drawingloadpath";
  public static final String PARAMETER_DEBUG 					= "debug";
  public static final String PARAMETER_EXTRACOLORS 				= "extracolors";
  public static final String PARAMETER_RESOURCESURL             = "resourcesurl";
  public static final String PARAMETER_DRAWINGBASETIME          = "drawingbasetime";
  
  public static final String RESOURCE_URL_INDICATOR 			= "%RESOURCE_URL%";

  public static final int SAVE_SUCCESS = 0;
  public static final int SAVE_FAILURE_PASSWORD=1;
  public static final int SAVE_FAILURE_CONCURRENTMODIFICATION=2;
  
  public String getPmWikiParameter(String parameter);
  public void setPmWikiParameter(String parameter, String value);

  public int saveDrawing(Drawing drawing);
  public URL createUrl(String filename) throws MalformedURLException;
  public void exit(boolean saved);
}
