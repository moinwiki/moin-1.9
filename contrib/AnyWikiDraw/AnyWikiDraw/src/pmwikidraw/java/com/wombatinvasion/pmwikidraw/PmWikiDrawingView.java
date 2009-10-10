/*
 * Created on 28-Nov-2004
 *
 * TODO To change the template for this generated file go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
package com.wombatinvasion.pmwikidraw;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Rectangle;
import java.awt.RenderingHints;
import java.awt.Stroke;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;

import javax.swing.SwingUtilities;

import org.jhotdraw.contrib.zoom.ZoomDrawingView;
import org.jhotdraw.figures.GroupCommand;
import org.jhotdraw.figures.UngroupCommand;
import org.jhotdraw.framework.DrawingEditor;
import org.jhotdraw.framework.DrawingView;
import org.jhotdraw.framework.Painter;
import org.jhotdraw.framework.PointConstrainer;
import org.jhotdraw.standard.CopyCommand;
import org.jhotdraw.standard.CutCommand;
import org.jhotdraw.standard.DeleteCommand;
import org.jhotdraw.standard.PasteCommand;
import org.jhotdraw.standard.StandardDrawingView;
import org.jhotdraw.standard.StandardDrawingView.DrawingViewKeyListener;
import org.jhotdraw.util.Command;
import org.jhotdraw.util.RedoCommand;
import org.jhotdraw.util.UndoCommand;
import org.jhotdraw.util.UndoableCommand;
import org.jhotdraw.standard.*;

/**
 * @author bob
 *
 * TODO To change the template for this generated type comment go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
public class PmWikiDrawingView extends StandardDrawingView {

	private static final long serialVersionUID = -1L;
	private boolean fQualityMode = true;
	private KeyListener keyListener = null;
	
	public PmWikiDrawingView(DrawingEditor editor, int width, int height) {
	  super(editor, width, height);
	  this.addBackground(new Painter() {
		/* (non-Javadoc)
		 * @see org.jhotdraw.framework.Painter#draw(java.awt.Graphics, org.jhotdraw.framework.DrawingView)
		 */
		public void draw(Graphics g, DrawingView view) {
			Rectangle bounds = g.getClipBounds();
			PointConstrainer pConstrainer = view.getConstrainer();
			if(bounds != null && pConstrainer != null) {
				int stepX = pConstrainer.getStepX();
				int stepY = pConstrainer.getStepY();
				int x = bounds.x + ( stepX - (bounds.x%(stepX))-stepX ); 
				int y = bounds.y + ( stepY - (bounds.y%(stepY))-stepY );
				g.setColor(Color.lightGray);
				int storedX=x ;
				int storedY=y;
				int endWidth = (bounds.x + bounds.width+stepX);
				int endHeight = ( bounds.y+bounds.height+stepY );
				Stroke originalStroke = ((Graphics2D)g).getStroke();
				((Graphics2D)g).setStroke(new BasicStroke(0.5f));
				while(y <= endHeight )  { // Horizontal lines.
					g.drawLine(x, y, x+ bounds.width+10, y );
					y+=(stepY);
				}
				x=storedX;
				y=storedY;
				while( x<=endWidth ) { // Vertical lines.
					g.drawLine(x, y, x, y +  bounds.height+10 );
					x+=(stepX);
				}
				((Graphics2D)g).setStroke(originalStroke);

			} 
		}
	});	  
	}
	/* (non-Javadoc)
	 * @see org.jhotdraw.standard.StandardDrawingView#drawDrawing(java.awt.Graphics)
	 */
	public void drawDrawing(Graphics g) {
		if(fQualityMode) {
			((Graphics2D)g).setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
			((Graphics2D)g).setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
		}
		super.drawDrawing(g);
	}
	
	public void setQualityMode(boolean qualityOn) {
		fQualityMode = qualityOn;
	}
	
	public boolean getQualityMode() {
		return fQualityMode;
	}
	
	public class PmWikiDrawingViewKeyListener extends DrawingViewKeyListener {
	  Command cutCmd  =new UndoableCommand(new CutCommand("Cut", editor()));
	  Command copyCmd  =new UndoableCommand(new CopyCommand("Copy", editor()));
	  Command pasteCmd  =new UndoableCommand(new PasteCommand("Paste", editor()));
	  Command duplicateCmd  =new UndoableCommand(new DuplicateCommand("Copy", editor()));
	  Command groupCmd = new UndoableCommand(new GroupCommand("Group", editor()));
	  Command unGroupCmd = new UndoableCommand(new UngroupCommand("UnGroup", editor()));
	  Command undo = new UndoCommand("Undo", editor());
	  Command redo = new RedoCommand("Undo", editor());
	   
	  /**
     * 
     */
    public PmWikiDrawingViewKeyListener()
    {
      super();
    }
		public void keyPressed(KeyEvent e) {
//			super.keyPressed(e);
			int code = e.getKeyCode();

			// modify Ctrl combinations
			if( ( e.getModifiers() & KeyEvent.CTRL_MASK) == KeyEvent.CTRL_MASK) {
			  switch(code) {
		    case  KeyEvent.VK_X:
					if (cutCmd.isExecutable())
						cutCmd.execute();
					break;
		    case  KeyEvent.VK_C:
					if (copyCmd.isExecutable())
						copyCmd.execute();
					break;
		    case  KeyEvent.VK_V:
					if (pasteCmd.isExecutable())
						pasteCmd.execute();
					break;
		    case  KeyEvent.VK_G:
					if (groupCmd.isExecutable())
						groupCmd.execute();
					break;
		    case  KeyEvent.VK_U:
					if (unGroupCmd.isExecutable())
						unGroupCmd.execute();
					break;
		    case  KeyEvent.VK_Z:
					if (undo.isExecutable())
						undo.execute();
					break;
		    case  KeyEvent.VK_Y:
					if (redo.isExecutable())
						redo.execute();
					break;
				case KeyEvent.VK_Q:
				  
			  default:
						super.keyPressed(e);
			  	  break;
			  }
			}
			else {
				super.keyPressed(e);
			}
		}
		
	}

	protected KeyListener createKeyListener() {
	  
		return new PmWikiDrawingViewKeyListener();
	}
}
