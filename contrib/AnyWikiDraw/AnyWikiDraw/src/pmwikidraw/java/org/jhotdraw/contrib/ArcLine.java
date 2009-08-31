package org.jhotdraw.contrib;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.Stroke;
import java.awt.geom.QuadCurve2D;
import java.util.List;

import org.jhotdraw.figures.LineConnection;
import org.jhotdraw.figures.PolyLineHandle;
import org.jhotdraw.framework.FigureAttributeConstant;
import org.jhotdraw.framework.HandleEnumeration;
import org.jhotdraw.standard.AbstractFigure;
import org.jhotdraw.standard.ChangeConnectionEndHandle;
import org.jhotdraw.standard.ChangeConnectionStartHandle;
import org.jhotdraw.standard.HandleEnumerator;
import org.jhotdraw.util.CollectionsFactory;

import com.wombatinvasion.pmwikidraw.PmWikiLineStyles;

import CH.ifa.draw.standard.AbstractHandle;
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
 * ArcLine
 */
public class ArcLine extends LineConnection
{
  private Point fControlPoint = new Point(0,0);
  private Float fLineWidth = new Float(1.0);
  
  /**
   * 
   */
  public ArcLine()
  { 
    super();
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.figures.PolyLineFigure#draw(java.awt.Graphics)
   */
  public void draw(Graphics g)
  {
    Graphics2D g2 = (Graphics2D)g;
    g.setColor(getFrameColor());
		Point p1, p2, p3;
		p1 = (Point)fPoints.get(0);
		p2 =  (Point)fPoints.get(1);
    QuadCurve2D quadCurve = new QuadCurve2D.Float(p1.x, p1.y, fControlPoint.x, fControlPoint.y, p2.x, p2.y);
		g2.draw(quadCurve);
  }
  
  /**
	 * Gets the handles of the figure. It returns the normal
	 * PolyLineHandles but adds ChangeConnectionHandles at the
	 * start and end.
	 */
	public HandleEnumeration handles() {
		List handles = CollectionsFactory.current().createList(fPoints.size());
		handles.add(new ChangeArcCurvatureHandle(this));
		handles.add(new ChangeConnectionStartHandle(this));
		for (int i = 1; i < fPoints.size()-1; i++) {
			handles.add(new PolyLineHandle(this, locator(i), i));
		}
		handles.add(new ChangeConnectionEndHandle(this));
		return new HandleEnumerator(handles);
	}

	
  //------------------------------------------------------------------------------
  /**
   * @return
   */
  public Point controlPoint()
  {
    return new Point(fControlPoint.x, fControlPoint.y);
  }  
  
  public void controlPoint(Point pt) {
    fControlPoint = new Point(pt.x, pt.y);
  }
	
  protected void basicMoveBy(int dx, int dy) {
	  super.basicMoveBy(dx,dy);
	  fControlPoint.translate(dx,dy);
	}
  
  /* (non-Javadoc)
   * @see org.jhotdraw.figures.PolyLineFigure#displayBox()
   */
  public Rectangle displayBox()
  {
    if(fPoints.size()>1) {
      Rectangle r = new Rectangle((Point)fPoints.get(0));
      r.add(fControlPoint);
      r.add((Point)fPoints.get(1));
      r.grow(AbstractHandle.HANDLESIZE, AbstractHandle.HANDLESIZE);
      return r;
    }
    else 
    {
      return new Rectangle(0,0);
    }
  }
  /**
   * @return Returns the fControlPoint.
   */
  public Point getControlPoint() {
  	return fControlPoint;
  }
  /* (non-Javadoc)
   * @see org.jhotdraw.figures.PolyLineFigure#containsPoint(int, int)
   */
  public boolean containsPoint(int x, int y)
  { // No real point creating a quadCurve all the time, I'll store one in future.
		Point p1, p2, p3;
		p1 = (Point)fPoints.get(0);
		p2 =  (Point)fPoints.get(1);
    QuadCurve2D quadCurve = new QuadCurve2D.Float(p1.x, p1.y, fControlPoint.x, fControlPoint.y, p2.x, p2.y);
    return quadCurve.contains(x,y);
  }
}
