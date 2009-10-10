/*
 * Created on 30-Dec-2004
 */
package com.wombatinvasion.pmwikidraw.gui;

import java.awt.Color;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.List;
import java.util.ListIterator;

import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JTabbedPane;

import org.jhotdraw.contrib.dnd.DragNDropTool;
import org.jhotdraw.contrib.dnd.JHDDragSourceListener;
import org.jhotdraw.contrib.dnd.JHDDropTargetListener;
import org.jhotdraw.figures.GroupFigure;
import org.jhotdraw.figures.TextFigure;
import org.jhotdraw.framework.Drawing;
import org.jhotdraw.framework.DrawingEditor;
import org.jhotdraw.framework.DrawingView;
import org.jhotdraw.framework.Tool;
import org.jhotdraw.framework.ViewChangeListener;
import org.jhotdraw.util.StorableInput;
import org.jhotdraw.util.UndoManager;

import qdxml.QDParser;

import com.wombatinvasion.pmwikidraw.PmWikiDrawing;
import com.wombatinvasion.pmwikidraw.PmWikiDrawingConverter;
import com.wombatinvasion.pmwikidraw.PmWikiDrawingView;
import com.wombatinvasion.pmwikidraw.symbol.SymbolPackage;
import com.wombatinvasion.pmwikidraw.symbol.SymbolPackage.Symbol;
import com.wombatinvasion.pmwikidraw.symbol.SymbolPackage.SymbolGroup;

/**
 * @author Ciaran Jessup
 */
public class SymbolPackageContainer extends JFrame implements DrawingEditor {

	private SymbolPackage symbolPackage = null;
    private DrawingView[] views = null;
    private JTabbedPane tabbedContainer = null;
    private Tool myTool = null;
    private UndoManager myUndoManager = new UndoManager();
    
    private class SymbolPackageContainerDrawingView extends PmWikiDrawingView {
    	/**
		 * 
		 */
		public SymbolPackageContainerDrawingView(DrawingEditor editor, int width, int height) {
			super(editor,width,height);
		}
		/* (non-Javadoc)
		 * @see org.jhotdraw.standard.StandardDrawingView#allowDropping()
		 */
		public boolean allowDropping() {
			return false;
		}
    }
    private String packageUrl;
	/**
	 * 
	 */
	public SymbolPackageContainer(String url) {
		super();
		try {
			packageUrl = url;
			retrieveResource();
			buildContent();
			this.setSize(400, 400);
			this.setVisible(true);
		} catch (Exception e) {
			e.printStackTrace();
		}
	}
	
	private void retrieveResource() throws  Exception {
		URL indexUrl = new URL("jar:"+packageUrl+"!/symbols.xml");
		URLConnection uc = indexUrl.openConnection();
		parseManifest(uc.getInputStream());
		this.setTitle("Symbols - " + symbolPackage.getName());
	}
	
	private void parseManifest(InputStream manifestXML) throws Exception {
		// Build SymbolPage object
		
		symbolPackage = new SymbolPackage();
		QDParser.parse(symbolPackage, new InputStreamReader(manifestXML));
	}
	
	private void buildContent() {
		List symbolGroups = symbolPackage.getSymbolGroups();
		if(symbolGroups.size()>1) {
			tabbedContainer = new JTabbedPane();
			List tempViews = new ArrayList();
			for(int i=0;i<symbolGroups.size();i++) {
				SymbolGroup symbolGroup = (SymbolGroup)symbolGroups.get(i);
				PmWikiDrawingView view = createSymbolGroupPane(symbolGroup);
				tabbedContainer.add(symbolGroup.name.toString(), new JScrollPane(view));
				tempViews.add(view);
			}
			views = new DrawingView[tempViews.size()];
			for(int i =0;i<tempViews.size();i++) {
				views[i] = (DrawingView)tempViews.get(i);
			}
			myTool = new DragNDropTool(this);
			
			for(int i =0;i<views.length;i++) {
				fireViewCreatedEvent(views[i]);
			}
			this.setContentPane(tabbedContainer);
			myTool.activate();
		} 
		else if(symbolGroups.size()==1){
			PmWikiDrawingView view = createSymbolGroupPane((SymbolGroup)symbolGroups.get(0)); 
			this.getContentPane().add(new JScrollPane(view));
			views = new DrawingView[1];
			views[0] = view;
			myTool = new DragNDropTool(this);
			myTool.activate();
			fireViewCreatedEvent(view);			
		}
		else {
			//do Nothing.
			System.err.println("Symbol Package appears to be empty ?!?!");
		}
	}

	/**
	 * @param group
	 */
	private PmWikiDrawingView createSymbolGroupPane(SymbolGroup group) {
		int viewWidth = 360;
		int viewHeight = 340;
		//Process the symbols contained in this group and calculate the offsets, widths etc.
		Drawing drawing = new PmWikiDrawing();
		int currentRowWidth = 6;
		int currentRowHeight = 6;
		int maxPreviousRowHeight = 0;
		PmWikiDrawingConverter converter = new PmWikiDrawingConverter();
		
		for(int i=0; i< group.symbols.size();i++) {
			Symbol symbol = (Symbol)group.symbols.get(i);
			if(symbol.location!=null && !symbol.location.equals("")) {
				Drawing symbolDrawing = null;
				try {
					URL indexUrl = new URL("jar:"+packageUrl+"!/"+symbol.location);
					URLConnection uc = indexUrl.openConnection();
					converter.convert(uc.getInputStream());
					StorableInput input = new StorableInput(converter.getConvertedStream());
					symbolDrawing = (Drawing)input.readStorable();
					GroupFigure groupFigure = new GroupFigure();
					groupFigure.addAll(symbolDrawing.figures());
					
					TextFigure figureName = new TextFigure();
					figureName.setText(symbol.name.toString());
					int figureWidth = 0;
					if(figureName.displayBox().width > groupFigure.displayBox().width) {
						// Text wider than symbol

						// Shove the label to the bottom.
						figureName.moveBy(0, groupFigure.displayBox().height+ 4);
						figureWidth = figureName.displayBox().width;
						//Center the drawing against the text.
						groupFigure.moveBy((figureName.displayBox().width/2) -(groupFigure.displayBox().width/2)  , 0);
					} else {
					    //Symbol wider than label
						figureName.moveBy((groupFigure.displayBox().width/2) - (figureName.displayBox().width/2), groupFigure.displayBox().height+ 4);
						figureWidth = groupFigure.displayBox().width;
					}
					//TODO: If a symbol is defined that is too large, this code will never print it..
					// Now move the symbol relative to all the other symbols currently on the drawing.
					if(currentRowWidth + figureWidth <= viewWidth ) {
						// We can fit this symbol on the current row.
						if( figureName.displayBox().y + figureName.displayBox().height >= maxPreviousRowHeight) {
							maxPreviousRowHeight = figureName.displayBox().y + figureName.displayBox().height; 
						}
						
						groupFigure.moveBy(currentRowWidth, currentRowHeight);
						figureName.moveBy(currentRowWidth, currentRowHeight);
						currentRowWidth += figureWidth;
						currentRowWidth += 6; // 5 pixel buffer between images.
					} else {
						// we need to move onto the next row.
						currentRowWidth = 6;
						currentRowHeight += maxPreviousRowHeight;
						currentRowHeight += 6;
						groupFigure.moveBy(currentRowWidth, currentRowHeight);
						figureName.moveBy(currentRowWidth, currentRowHeight);
						currentRowWidth += figureWidth;
						currentRowWidth += 6; // 5 pixel buffer between images.
						maxPreviousRowHeight =0;
					}
					
					drawing.add(groupFigure);
					drawing.add(figureName);
					figureName.setReadOnly(true);
					
			
				} catch (FileNotFoundException e) {
					e.printStackTrace();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}
		
		SymbolPackageContainerDrawingView view = new SymbolPackageContainerDrawingView(this, viewWidth, viewHeight);
		view.setBackground(Color.white);
		view.setDrawing(drawing);
		return view;
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.DrawingEditor#view()
	 */
	public DrawingView view() {
		if(tabbedContainer == null) {
			return (DrawingView)views[0];
		} else {
			return (DrawingView)views[tabbedContainer.getSelectedIndex()];
		}
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.DrawingEditor#views()
	 */
	public DrawingView[] views() {
		return views;
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.DrawingEditor#tool()
	 */
	public Tool tool() {
		return myTool;
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.DrawingEditor#toolDone()
	 */
	public void toolDone() {
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.DrawingEditor#figureSelectionChanged(org.jhotdraw.framework.DrawingView)
	 */
	public void figureSelectionChanged(DrawingView view) {
	}
	private List listeners = new ArrayList();
	
	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.DrawingEditor#addViewChangeListener(org.jhotdraw.framework.ViewChangeListener)
	 */
	public void addViewChangeListener(ViewChangeListener vsl) {
		listeners.add(vsl);
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.DrawingEditor#removeViewChangeListener(org.jhotdraw.framework.ViewChangeListener)
	 */
	public void removeViewChangeListener(ViewChangeListener vsl) {
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.DrawingEditor#showStatus(java.lang.String)
	 */
	public void showStatus(String string) {
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.framework.DrawingEditor#getUndoManager()
	 */
	public UndoManager getUndoManager() {
		return myUndoManager;
	}
	
	protected void fireViewCreatedEvent(DrawingView view) {
		ListIterator li= listeners.listIterator(listeners.size());
		while (li.hasPrevious()) {
			ViewChangeListener vsl = (ViewChangeListener)li.previous();
			vsl.viewCreated(view);
		}
	}
	
}
