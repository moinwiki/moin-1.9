/*
 * Created on 27-Nov-2004
 *
 * TODO To change the template for this generated file go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
package com.wombatinvasion.pmwikidraw;

import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Image;
import java.awt.MediaTracker;
import java.awt.event.MouseEvent;

import javax.swing.ImageIcon;

import org.jhotdraw.framework.JHotDrawRuntimeException;
import org.jhotdraw.util.Command;
import org.jhotdraw.util.Iconkit;
import org.jhotdraw.util.PaletteButton;
import org.jhotdraw.util.PaletteIcon;
import org.jhotdraw.util.PaletteListener;


/**
 * @author bob
 *
 */
public class CommandButton extends PaletteButton {

	private static final long serialVersionUID = 1L;

	private PaletteIcon fIcon;
	
	private Command fCommand;
	public CommandButton(PaletteListener listener, String iconName, String name) {
		this(listener, iconName, name, null);
	}
	
	/**
	 * @param listener
	 */
	public CommandButton(PaletteListener listener, String iconName, String name, Command command) {
		super(listener);

		// use a Mediatracker to ensure that all the images are initially loaded
		Iconkit kit = Iconkit.instance();
		if (kit == null) {
			throw new JHotDrawRuntimeException("Iconkit instance isn't set");
		}

		Image im[] = new Image[4];
		im[0] = kit.loadImageResource(iconName+"1.gif");
		im[1] = kit.loadImageResource(iconName+"2.gif");
		im[2] = kit.loadImageResource(iconName+"3.gif");
		im[3] = kit.loadImageResource(iconName+"4.gif");
		
		MediaTracker tracker = new MediaTracker(this);
		for (int i = 0; i < 4; i++) {
			tracker.addImage(im[i], i);
		}
		try {
			tracker.waitForAll();
		}
		catch (Exception e) {
			// ignore exception
		}

		setPaletteIcon(new PaletteIcon(new Dimension(24,24), im[0], im[1], im[2]));
		setCommand(command);
		setName(name);

		// avoid null pointer exception if image could not be loaded
		if (im[0] != null) {
			setIcon(new ImageIcon(im[0]));
		}
		if (im[1] != null) {
			setPressedIcon(new ImageIcon(im[1]));
		}
		if (im[2] != null) {
			setSelectedIcon(new ImageIcon(im[2]));
		}
		if (im[3] != null) {
			setDisabledIcon(new ImageIcon(im[3]));
		}
		setToolTipText(name);
	}


	
	public void paintSelected(Graphics g) {
		if (getPaletteIcon().selected() != null) {
			g.drawImage(getPaletteIcon().selected(), 0, 0, this);
		}
	}

	public void paint(Graphics g) {
		// selecting does not work as expected with JFC1.1
		// see JavaBug: 4228035, 4233965
		if (isSelected()) {
			paintSelected(g);
		}
		else {
			super.paint(g);
		} 
	}	
	
	public void mouseClicked(MouseEvent e) {
		if(fCommand.isExecutable()) {
			fCommand.execute();
		}
	}
	protected PaletteIcon getPaletteIcon() {
		return fIcon;
	}

	private void setPaletteIcon(PaletteIcon newIcon) {
		fIcon = newIcon;
	}
	public Dimension getMinimumSize() {
		return new Dimension(getPaletteIcon().getWidth(), getPaletteIcon().getHeight());
	}

	public Dimension getPreferredSize() {
		return new Dimension(getPaletteIcon().getWidth(), getPaletteIcon().getHeight());
	}

	public Dimension getMaximumSize() {
		return new Dimension(getPaletteIcon().getWidth(), getPaletteIcon().getHeight());
	}
	
	public void setCommand(Command cmd) {
		fCommand = cmd;
	}
	
	public String name() {
		return getName();
	}
	/* (non-Javadoc)
	 * @see java.awt.Component#isEnabled()
	 */
	public boolean isEnabled() {
		if( fCommand != null ) {
			return fCommand.isExecutable();
		}
		else {
			return false;
		}
	}
}
