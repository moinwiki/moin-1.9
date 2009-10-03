/*
 * @(#)GroupFigure.java
 *
 * Project:		JHotdraw - a GUI framework for technical drawings
 *				http://www.jhotdraw.org
 *				http://jhotdraw.sourceforge.net
 * Copyright:	© by the original author(s) and all contributors
 * License:		Lesser GNU Public License (LGPL)
 *				http://www.opensource.org/licenses/lgpl-license.html
 */

package org.jhotdraw.figures;

import java.awt.*;
import java.util.List;
import java.util.Vector;

import org.jhotdraw.framework.*;
import org.jhotdraw.standard.*;
import org.jhotdraw.util.CollectionsFactory;


/**
 * A Figure that groups a collection of figures.
 *
 * @version <$CURRENT_VERSION$>
 */
public  class GroupFigure extends CompositeFigure {

	/*
	 * Serialization support.
	 */
	private static final long serialVersionUID = 8311226373023297933L;
	private int groupFigureSerializedDataVersion = 1;

   /**
	* GroupFigures cannot be connected //CJ: or can they ;)
	*/
	public boolean canConnect() {
		return true;
	}

   /**
	* Gets the display box. The display box is defined as the union
	* of the contained figures.
	*/
	public Rectangle displayBox() {
		FigureEnumeration fe = figures();
		Rectangle r = fe.nextFigure().displayBox();

		while (fe.hasNextFigure()) {
			r.add(fe.nextFigure().displayBox());
		}
		return r;
	}

	public void basicDisplayBox(Point origin, Point corner) {
   /* Scaling code from original Pmwikidraw, not great, gah not sure how to fix...
	  Rectangle srcr = displayBox();
    Rectangle dstr = new Rectangle(origin.x, origin.y, corner.x - origin.x,
        corner.y - origin.y);

    if (srcr.equals(dstr) || corner.x <= origin.x || corner.y <= origin.y)
      return;

    // Scaling transform
    double xtx = (double) (corner.x - origin.x) / srcr.width;
    double ytx = (double) (corner.y - origin.y) / srcr.height;
    
    if(xtx<1 || ytx<1) 
      return;
    
    xtx = (int)xtx;
    ytx = (int)ytx;
    
    FigureEnumeration k = figures();
    while (k.hasNextFigure())
    {
      Figure child = k.nextFigure();
      Rectangle sr = child.displayBox();
      Point childOrigin = new Point((int) Math.round(dstr.x + (sr.x - srcr.x)
          * xtx), (int) Math.round(dstr.y + (sr.y - srcr.y) * ytx));
      Point childCorner = new Point((int) Math.round(childOrigin.x + sr.width
          * xtx), (int) Math.round(childOrigin.y + sr.height * ytx));
      child.displayBox(childOrigin, childCorner);
    } */
	}

	public FigureEnumeration decompose() {
		return new FigureEnumerator(fFigures);
	}

   /**
	* Gets the handles for the GroupFigure.
	*/
	public HandleEnumeration handles() {
// Scaling code from original PmWikiDraw.
/*    Vector handles = new Vector();
  	// Handles changed to standard handles to support group scaling
  	// Crawford Currie, Motorola
  	BoxHandleKit.addCornerHandles(this, handles);
  */	
	  List handles = CollectionsFactory.current().createList();
		handles.add(new GroupHandle(this, RelativeLocator.northWest()));
		handles.add(new GroupHandle(this, RelativeLocator.northEast()));
		handles.add(new GroupHandle(this, RelativeLocator.southWest()));
		handles.add(new GroupHandle(this, RelativeLocator.southEast()));
		return new HandleEnumerator(handles);
	}

   /**
	* Sets the attribute of all the contained figures.
	* @deprecated see setAttribute(FigureAttributeConstant,Object)
	*/
	public void setAttribute(String name, Object value) {
		super.setAttribute(name, value);
		FigureEnumeration fe = figures();
		while (fe.hasNextFigure()) {
			fe.nextFigure().setAttribute(name, value);
		}
	}

	/**
	 * Sets the attribute of the GroupFigure as well as all contained Figures.
	 */
	public void setAttribute(FigureAttributeConstant fac, Object object){
		super.setAttribute(fac, object);
		FigureEnumeration fe = figures();
		while (fe.hasNextFigure()) {
			fe.nextFigure().setAttribute(fac, object);
		}		
	}
}
