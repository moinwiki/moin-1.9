/*
 * @(#)FileIconsSample.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.samples.mini;

import java.awt.*;
import java.awt.geom.*;
import java.awt.image.*;
import java.io.File;
import javax.swing.*;
import javax.swing.filechooser.FileSystemView;
import org.jhotdraw.draw.*;
import org.jhotdraw.geom.*;
import static org.jhotdraw.draw.AttributeKeys.*;

/**
 * Example showing how to lay out composite figures.
 *
 * @author Werner Randelshofer
 * @version $Id: FileIconsSample.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class FileIconsSample {

    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {

            public void run() {
                // Let the user choose a directory
                JFileChooser fc = new JFileChooser();
                fc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
                fc.setDialogTitle("Choose a directory");
                if (fc.showOpenDialog(null) != JFileChooser.APPROVE_OPTION) {
                    System.exit(0);
                }


                // Create a drawing
                Drawing drawing = new DefaultDrawing();

                // Add a figure for each file to the drawing
                File dir = fc.getSelectedFile();
                File[] files = dir.listFiles();
                FileSystemView fsv = FileSystemView.getFileSystemView();
                int maxColumn = Math.max((int) Math.sqrt(files.length), 1);
                double tx = 0;
                double ty = 0;
                double rowHeight = 0;
                int i = 0;
                for (File f : files) {
                    // Create an image figure for the file icon
                    Icon icon = fsv.getSystemIcon(f);
                    BufferedImage bimg = new BufferedImage(icon.getIconWidth(), icon.getIconHeight(), BufferedImage.TYPE_INT_ARGB);
                    Graphics2D g = bimg.createGraphics();
                    icon.paintIcon(null, g, 0, 0);
                    g.dispose();
                    ImageFigure imf = new ImageFigure();
                    imf.setBufferedImage(bimg);
                    STROKE_COLOR.set(imf, null);
                    imf.setBounds(new Point2D.Double(0,0),new Point2D.Double(icon.getIconWidth(), icon.getIconHeight()));
                    
                    // Creata TextAreaFigure for the file name
                    // We limit its width to 100 Pixels
                    TextAreaFigure tef = new TextAreaFigure(f.getName());
                    Dimension2DDouble dim = tef.getPreferredTextSize(100);
                    Insets2D.Double insets = tef.getInsets();
                    tef.setBounds(new Point2D.Double(0,0), 
                            new Point2D.Double(Math.max(100,dim.width)+insets.left+insets.right, 
                            dim.height+insets.top+insets.bottom));
                    STROKE_COLOR.set(tef, null);
                    FILL_COLOR.set(tef, null);
                    TEXT_ALIGNMENT.set(tef, Alignment.CENTER);

                     
                    // Alternatively, you could just create a TextFigure
                    /*
                    TextFigure tef = new TextFigure(f.getName());
                    */
                    
                    // Create a GraphicalCompositeFigure with vertical layout
                    // and add the icon and the text figure to it
                    GraphicalCompositeFigure gcf = new GraphicalCompositeFigure();
                    gcf.setLayouter(new VerticalLayouter());
                    COMPOSITE_ALIGNMENT.set(gcf, Alignment.CENTER);
                    gcf.add(imf);
                    gcf.add(tef);
                    gcf.layout();

                    // Lay out the graphical composite figures on the drawing
                    if (i++ % maxColumn == 0) {
                        ty += rowHeight + 20;
                        tx = 0;
                        rowHeight = 0;
                    }
                    Rectangle2D.Double b = gcf.getBounds();
                    rowHeight = Math.max(rowHeight, b.height);
                    
                    AffineTransform at = new AffineTransform();
                    at.translate(tx, ty);
                    gcf.transform(at);
                    
                    tx += b.width + 20;
                    
                    drawing.add(gcf);
                 }

                // Show the drawing
                JFrame f = new JFrame("Contents of directory "+dir.getName());
                f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
                f.setSize(400, 300);

                DrawingView view = new DefaultDrawingView();
                view.setDrawing(drawing);
                f.getContentPane().add(view.getComponent());
                DrawingEditor editor = new DefaultDrawingEditor();
                editor.setTool(new DelegationSelectionTool());
                editor.add(view);
                editor.setActiveView(view);

                f.show();
            }
        });
    }
}
