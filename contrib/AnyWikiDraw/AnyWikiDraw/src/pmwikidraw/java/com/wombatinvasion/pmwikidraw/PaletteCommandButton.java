/*
 * Created on 24-Feb-2005
 *
 * TODO To change the template for this generated file go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
package com.wombatinvasion.pmwikidraw;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.event.MouseEvent;

import javax.swing.SwingUtilities;

import org.jhotdraw.figures.AttributeFigure;
import org.jhotdraw.framework.DrawingEditor;
import org.jhotdraw.framework.FigureAttributeConstant;
import org.jhotdraw.util.Command;
import org.jhotdraw.util.PaletteListener;
import org.jhotdraw.util.UndoableCommand;

/**
 * @author bob
 *
 * TODO To change the template for this generated type comment go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
public class PaletteCommandButton extends CommandButton {
   
  private final FigureAttributeConstant constant;
  private final UndoableCommand undoableColourChanger;
  private final ColorPaletteChangeAttributeCommand colourChanger;
   
	/**
	 * @param listener
	 * @param iconName
	 * @param name
	 * @param constant
	 */
	public PaletteCommandButton(PaletteListener listener, String iconName,String name, FigureAttributeConstant constant, DrawingEditor editor) {
		super(listener, iconName, name);
		this.constant = constant;
		colourChanger = new ColorPaletteChangeAttributeCommand("Select...", constant, editor);
		undoableColourChanger = new UndoableCommand(colourChanger);
		setCommand(colourChanger);
	}
	
	/* (non-Javadoc)
	 * @see javax.swing.JComponent#paintChildren(java.awt.Graphics)
	 */
	protected void paintChildren(Graphics g) {
		// Draw button background
    g.setColor(java.awt.Color.lightGray);
		g.fill3DRect(2,2, g.getClipBounds().width-4, g.getClipBounds().height-4, true);

    Object colour = AttributeFigure.getDefaultAttribute(constant);
    if ( colour == null || !( colour instanceof Color ) ) {
      colour = Color.black;
    }
    g.setColor((Color)colour);
    
    if ( constant == FigureAttributeConstant.FILL_COLOR ) {
      // Draw a filled square.
		  g.fillRect(6,6, g.getClipBounds().width-12, g.getClipBounds().height-12);
    }
    else if ( constant == FigureAttributeConstant.TEXT_COLOR ) {
      g.setColor(java.awt.Color.black);
      g.drawString("A", (int)((g.getClipBounds().width/2) -4), g.getClipBounds().height-10);
      
      g.setColor((Color)colour);
      g.fillRect(6,g.getClipBounds().height-8, g.getClipBounds().width-12, 4);
    }
    else {
       // Draw a box outline.
      g.drawRect(6,6, g.getClipBounds().width-12, g.getClipBounds().height-12);
    }
		super.paintChildren(g);
	}
  public void mouseClicked(MouseEvent e) {
    if ( isEnabled() && SwingUtilities.isRightMouseButton(e) ) {
      super.mouseClicked(e);
    }
    else {
      colourChanger.setOnlyChangeMode(true);
      undoableColourChanger.execute();
      colourChanger.setOnlyChangeMode(false);
    }
  }
}
