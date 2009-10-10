package org.jhotdraw.contrib;

import java.awt.Graphics;
import java.awt.Point;
import java.awt.Rectangle;
import java.io.IOException;
import java.util.Vector;

import org.jhotdraw.figures.PolyLineFigure;

import org.jhotdraw.figures.AttributeFigure;
import org.jhotdraw.framework.ConnectionFigure;
import org.jhotdraw.framework.Connector;
import org.jhotdraw.framework.Figure;
import org.jhotdraw.framework.FigureAttributeConstant;
import org.jhotdraw.framework.FigureChangeEvent;
import org.jhotdraw.framework.FigureChangeListener;
import org.jhotdraw.framework.FigureEnumeration;
import org.jhotdraw.framework.HandleEnumeration;
import org.jhotdraw.standard.ChopBoxConnector;
import org.jhotdraw.util.StorableInput;
import org.jhotdraw.util.StorableOutput;
/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2004</p>
 * @author Ciaran Jessup
 * @version 1.0
 */

/*
 *  Modified:
 *   23-Nov-2004	cj       Initial development
 */

//------------------------------------------------------------------------------
/**
 * AttributeLineFigure
 */
public class AttributeLineFigure extends AttributeFigure implements FigureChangeListener
{
  protected PolyLineFigure fLine = null;
  
  public AttributeLineFigure() {
    super();
  }
  
  /**
   * 
   */
  public AttributeLineFigure(PolyLineFigure line )
  {
    super();
    fLine = line;
    fLine.addFigureChangeListener(this);
  }
  

  /* (non-Javadoc)
   * @see CH.ifa.draw.standard.AbstractFigure#basicMoveBy(int, int)
   */
  protected void basicMoveBy(int dx, int dy)
  {
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
    fLine.moveBy(dx,dy);
  }

  /* (non-Javadoc)
   * @see CH.ifa.draw.framework.Figure#basicDisplayBox(java.awt.Point, java.awt.Point)
   */
  public void basicDisplayBox(Point origin, Point corner)
  {
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
    fLine.displayBox(origin,corner);
  }

  /* (non-Javadoc)
   * @see CH.ifa.draw.framework.Figure#displayBox()
   */
  public Rectangle displayBox()
  {
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
    return fLine.displayBox();
  }

	/* (non-Javadoc)
	 * @see org.jhotdraw.standard.AbstractFigure#handles()
	 */
	public HandleEnumeration handles()
	{
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
	  return fLine.handles();
	}  
  
  /* (non-Javadoc)
   * @see CH.ifa.draw.standard.AbstractFigure#clone()
   */
  public Object clone()
  {
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
    return new AttributeLineFigure((PolyLineFigure)fLine.clone());
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.figures.AttributeFigure#drawFrame(java.awt.Graphics)
   */
  protected void drawFrame(Graphics g)
  {
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
    fLine.draw(g);
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.figures.AttributeFigure#write(org.jhotdraw.util.StorableOutput)
   */
  public void write(StorableOutput dw)
  {
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
    super.write(dw);
		dw.writeStorable(fLine);
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.figures.AttributeFigure#read(org.jhotdraw.util.StorableInput)
   */
  public void read(StorableInput dr) throws IOException
  {
    super.read(dr);
    fLine = (PolyLineFigure) dr.readStorable();
    fLine.addFigureChangeListener(this);
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.figures.AttributeFigure#getMap()
   */
  public String getMap()
  {
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
    return fLine.getMap();
  }
  /* (non-Javadoc)
   * @see org.jhotdraw.standard.AbstractFigure#changed()
   */
 /* public void changed()
  {
    invalidate();
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
    super.changed();
    fLine.changed();
  }
  */
  /* (non-Javadoc)
   * @see org.jhotdraw.standard.AbstractFigure#invalidate()
   */
  /*public void invalidate()
  {
    if(fLine == null) 
      throw new IllegalStateException("Nested Line not yet properly defined.");
    super.invalidate();
    fLine.invalidate();
  }
	 */
  /* (non-Javadoc)
	 * @see org.jhotdraw.framework.FigureChangeListener#figureChanged(org.jhotdraw.framework.FigureChangeEvent)
	 */
	public void figureChanged(FigureChangeEvent e)
	{
/*	  if(listener() != null && e.getFigure() != fLine) {
	    listener().figureChanged(e);
	  }
	  */ //Do Nothing 
	}
	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.FigureChangeListener#figureInvalidated(org.jhotdraw.framework.FigureChangeEvent)
	 */
	public void figureInvalidated(FigureChangeEvent e)
	{
	  if(listener() != null) {
	    listener().figureInvalidated(e);
	  }
	}
	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.FigureChangeListener#figureRemoved(org.jhotdraw.framework.FigureChangeEvent)
	 */
	public void figureRemoved(FigureChangeEvent e)
	{
	  if(listener() != null) {
	    listener().figureRemoved(e);
	  }
	}
	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.FigureChangeListener#figureRequestRemove(org.jhotdraw.framework.FigureChangeEvent)
	 */
	public void figureRequestRemove(FigureChangeEvent e)
	{
	  if(listener() != null) {
	    listener().figureRequestRemove(e);
	  }
	}
	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.FigureChangeListener#figureRequestUpdate(org.jhotdraw.framework.FigureChangeEvent)
	 */
	public void figureRequestUpdate(FigureChangeEvent e)
	{
	  if(listener() != null) {
	    listener().figureRequestUpdate(e);
	  }
	}
	
	/* (non-Javadoc)
   * @see org.jhotdraw.figures.AttributeFigure#setAttribute(org.jhotdraw.framework.FigureAttributeConstant, java.lang.Object)
   */
  public void setAttribute(FigureAttributeConstant attributeConstant,
      Object value)
  {
    super.setAttribute(attributeConstant, value);
    fLine.setAttribute(attributeConstant, value);
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.standard.AbstractFigure#containsPoint(int, int)
   */
  public boolean containsPoint(int x, int y)
  {
    return fLine.containsPoint(x, y);
  }

  public void addPoint(int x, int y) {
    fLine.addPoint(x,y);
  }

	  /* (non-Javadoc)
	 * @see org.jhotdraw.standard.AbstractFigure#getZValue()
	 */
	public int getZValue() {
		
		return fLine.getZValue();
	}
	
	
	/* (non-Javadoc)
	 * @see org.jhotdraw.standard.AbstractFigure#getDependendFigures()
	 */
	public synchronized FigureEnumeration getDependendFigures() {
		
		return fLine.getDependendFigures();
	}
	
	/* (non-Javadoc)
	 * @see org.jhotdraw.standard.AbstractFigure#setZValue(int)
	 */
	public void setZValue(int z) {
		fLine.setZValue(z);
	}
	
	/* (non-Javadoc)
	 * @see org.jhotdraw.standard.AbstractFigure#findFigureInside(int, int)
	 */
	public Figure findFigureInside(int x, int y) {
		return fLine.findFigureInside(x, y);
	}
    /* (non-Javadoc)
	 * @see org.jhotdraw.standard.AbstractFigure#release()
	 */
	public void release() {
		super.release();
		fLine.release();
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.standard.AbstractFigure#isEmpty()
	 */
	public boolean isEmpty() {
	
		return fLine.isEmpty();
	}
}
