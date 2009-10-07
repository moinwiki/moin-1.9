package org.jhotdraw.contrib;

import java.awt.Point;
import java.io.IOException;

import org.jhotdraw.figures.LineConnection;
import org.jhotdraw.framework.ConnectionFigure;
import org.jhotdraw.framework.Connector;
import org.jhotdraw.framework.Figure;
import org.jhotdraw.framework.FigureEnumeration;
import org.jhotdraw.util.StorableInput;

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
 * AttributeConnectorFigure
 */
public class AttributeConnectorFigure extends AttributeLineFigure implements ConnectionFigure
{

  private LineConnection fConnector = null;

  /**
   * 
   */
  public AttributeConnectorFigure()
  {
    super();
    fConnector = null;
  }

  /**
   * @param line
   */
  public AttributeConnectorFigure(LineConnection line)
  {
    super(line);
    fConnector = line;
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#connectStart(org.jhotdraw.framework.Connector)
   */
  public void connectStart(Connector start)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    fConnector.connectStart(start);
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#connectEnd(org.jhotdraw.framework.Connector)
   */
  public void connectEnd(Connector end)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    fConnector.connectEnd(end);    
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#updateConnection()
   */
  public void updateConnection()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    fConnector.updateConnection();
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#disconnectStart()
   */
  public void disconnectStart()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    fConnector.disconnectStart();
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#disconnectEnd()
   */
  public void disconnectEnd()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    fConnector.disconnectEnd();
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#getStartConnector()
   */
  public Connector getStartConnector()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.getStartConnector();
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#getEndConnector()
   */
  public Connector getEndConnector()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.getEndConnector();
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#canConnect(org.jhotdraw.framework.Figure, org.jhotdraw.framework.Figure)
   */
  public boolean canConnect(Figure start, Figure end)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.canConnect(start,end);
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#connectsSame(org.jhotdraw.framework.ConnectionFigure)
   */
  public boolean connectsSame(ConnectionFigure other)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.connectsSame(other);
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#startPoint(int, int)
   */
  public void startPoint(int x, int y)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    fConnector.startPoint(x,y);
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#endPoint(int, int)
   */
  public void endPoint(int x, int y)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    fConnector.endPoint(x,y);
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#startPoint()
   */
  public Point startPoint()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.startPoint();
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#endPoint()
   */
  public Point endPoint()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.endPoint();
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#setPointAt(java.awt.Point, int)
   */
  public void setPointAt(Point p, int index)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
   fConnector.setPointAt(p, index); 
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#pointAt(int)
   */
  public Point pointAt(int index)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.pointAt(index);
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#pointCount()
   */
  public int pointCount()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.pointCount();
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#splitSegment(int, int)
   */
  public int splitSegment(int x, int y)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.splitSegment(x,y);
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#joinSegments(int, int)
   */
  public boolean joinSegments(int x, int y)
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.joinSegments(x,y);
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#startFigure()
   */
  public Figure startFigure()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.startFigure();
  }

  /* (non-Javadoc)
   * @see org.jhotdraw.framework.ConnectionFigure#endFigure()
   */
  public Figure endFigure()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return fConnector.endFigure();
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.util.Storable#read(org.jhotdraw.util.StorableInput)
   */
  public void read(StorableInput dr) throws IOException
  {
    super.read(dr);
    fConnector = (LineConnection)fLine;
  }

  /* (non-Javadoc)
   * @see CH.ifa.draw.standard.AbstractFigure#clone()
   */
  public Object clone()
  {
    if(fConnector == null) 
      throw new IllegalStateException("Nested Connector not yet properly defined.");
    return new AttributeConnectorFigure((LineConnection)fConnector.clone());
  }
  
  
}
