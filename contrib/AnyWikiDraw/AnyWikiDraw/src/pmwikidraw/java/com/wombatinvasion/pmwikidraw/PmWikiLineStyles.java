package com.wombatinvasion.pmwikidraw;

import java.util.ArrayList;
import java.util.List;

import org.jhotdraw.framework.FigureAttributeConstant;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2004</p>
 * @author Ciaran Jessup
 * @version 1.0
 */

/*
 *  Modified:
 *   19-Nov-2004	cj       Initial development
 */

//------------------------------------------------------------------------------
/**
 * PmWikiLineStyles
 */
public class PmWikiLineStyles
{
  private final String styleName;
  private final float[] styleDash;
  private final int styleId;

  /** Holds an array of available line styles.
  */
  private static List pmWikiLineStyles = new ArrayList(4);
  public static final PmWikiLineStyles SOLID_LINE_STYLE = new PmWikiLineStyles("penStyleSolid",new float[]{1,0}, 1);

  public static final PmWikiLineStyles DASHED_LINE_STYLE = new PmWikiLineStyles("penStyleDashed",new float[]{25,25}, 2);
	
  public static final PmWikiLineStyles DASHED_N_DOTTED_LINE_STYLE = new PmWikiLineStyles("penStyleDashedDotted",new float[]{21,9,3,9}, 3);

  public static final PmWikiLineStyles DOTTED_LINE_STYLE = new PmWikiLineStyles("penStyleDotted",new float[]{3,3}, 4);
  
  /**
   *  Disable constructin of this object 
   */
  private PmWikiLineStyles(String style, float[] dash, int id){
    addLineStyle(this);
    styleName = style;
    styleDash = dash;
    styleId = id;
  } 
  
  public String getName() {
    return styleName;
  }
  
  public float[] getDash() {
    return styleDash;
  }
  
  public int getId() {
    return styleId;
  }
  
  public static List getLineStyles() { return pmWikiLineStyles; }
  
  public static int lineStylesCount() { return pmWikiLineStyles.size(); }
  
  public static void addLineStyle(PmWikiLineStyles style) { pmWikiLineStyles.add(style); } 

}
