package com.wombatinvasion.pmwikidraw;

import java.awt.event.MouseEvent;

import org.jhotdraw.figures.TextTool;
import org.jhotdraw.framework.DrawingEditor;
import org.jhotdraw.framework.DrawingView;
import org.jhotdraw.framework.Figure;
import org.jhotdraw.standard.SelectionTool;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2005</p>
 * @author Ciaran Jessup
 * @version 1.0
 */

/*
 *  Modified:
 *   09-Mar-2005	cj       Initial development
 */

//------------------------------------------------------------------------------
/**
 * PmWikiDrawSelectionTool
 */
public class PmWikiDrawSelectionTool extends SelectionTool
{

  public PmWikiDrawSelectionTool(DrawingEditor newDrawingEditor) {
    super(newDrawingEditor);
  }

  /**
   * Handles mouse down events and starts the corresponding tracker.
   */
  public void mouseDown(MouseEvent e, int x, int y) {
    setView((DrawingView)e.getSource());
    if (e.getClickCount() == 2) {
      Figure figure = drawing().findFigure(e.getX(), e.getY());
      if (figure != null) {
        inspectFigure(figure);
        return;
      }
    }
    super.mouseDown(e, x, y);
  }

  protected void inspectFigure(Figure f) {
    System.out.println("inspect figure"+f);
  }
}
