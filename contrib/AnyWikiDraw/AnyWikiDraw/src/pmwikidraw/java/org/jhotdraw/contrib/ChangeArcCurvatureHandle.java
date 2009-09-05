package org.jhotdraw.contrib;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Point;
import java.awt.Rectangle;

import org.jhotdraw.framework.DrawingView;
import org.jhotdraw.framework.Figure;
import org.jhotdraw.standard.AbstractHandle;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2004</p>
 * @author Ciaran Jessup
 * @version 1.0
 */

/*
 *  Modified:
 *   18-Nov-2004	cj       Initial development
 */

//------------------------------------------------------------------------------
/**
 * ChangeArcCurvatureHandle
 */
public class ChangeArcCurvatureHandle extends AbstractHandle
{
  private final ArcLine myArc;
  /**
   * 
   */
  public ChangeArcCurvatureHandle(ArcLine arcLine)
  {
    super(arcLine);
    myArc = arcLine;
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.standard.AbstractHandle#invokeStep(int, int, int, int, org.jhotdraw.framework.DrawingView)
   */
  public void invokeStep(int x, int y, int anchorX, int anchorY,
      DrawingView view)
  {
    super.invokeStep(x, y, anchorX, anchorY, view);
    Point ep = myArc.endPoint();
    myArc.invalidate();
    myArc.controlPoint(new Point(x, y));
    myArc.changed();
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.framework.Handle#locate()
   */
  public Point locate()
  {
    Point cp = myArc.controlPoint();
    return new Point(cp.x, cp.y);
  }
	
  /**
	 * Draws this handle.
	 * @see org.jhotdraw.framework.Handle#draw(java.awt.Graphics)
	 */
	public void draw(Graphics g) {
		Rectangle r = displayBox();
		Point ep = myArc.endPoint();
		g.setColor(Color.black);
		g.drawLine(r.x+(r.width/2), r.y+(r.height/2), ep.x,ep.y);
		g.setColor(Color.yellow);
		g.fillRect(r.x, r.y, r.width, r.height);

		g.setColor(Color.black);
		g.drawRect(r.x, r.y, r.width, r.height);
	}  
  
}
