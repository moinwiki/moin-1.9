package com.wombatinvasion.pmwikidraw;

import java.io.IOException;

import org.jhotdraw.framework.Figure;
import org.jhotdraw.framework.FigureEnumeration;
import org.jhotdraw.standard.StandardDrawing;
import org.jhotdraw.util.CollectionsFactory;
import org.jhotdraw.util.StorableInput;
import org.jhotdraw.util.StorableOutput;
/**
 * <p>Title: PmWikiDrawing</p>
 * <p>Description: A simple extension to Standard drawing to allow for drawing versioning.</p>
 * <p>Copyright: Copyright (c) 2004</p>
 * @author Ciaran Jessup
 * @version 1.0
 */

/*
 *  Modified:
 *   06-Dec-2004	cj       Initial development
 */

//------------------------------------------------------------------------------
/**
 * PmWikiDrawing
 */
public class PmWikiDrawing extends StandardDrawing
{
  public static final int VERSION = 2; 
  
  /**
   * 
   */
  public PmWikiDrawing()
  {
    super();
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.standard.CompositeFigure#write(org.jhotdraw.util.StorableOutput)
   */
  public void write(StorableOutput dw)
  {
		dw.writeInt(VERSION);
		super.write(dw);
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.standard.CompositeFigure#read(org.jhotdraw.util.StorableInput)
   */
  public void read(StorableInput dr) throws IOException
  {
    dr.readInt(); //version
		int size = dr.readInt(); //element count
		fFigures = CollectionsFactory.current().createList(size);
		for (int i=0; i<size; i++) {
		  Figure figure = (Figure)dr.readStorable();
			add(figure);
		}
		init(displayBox());
  }
}
