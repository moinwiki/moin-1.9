/*
 * @(#)LayouterSample.java
 *
 * Copyright (c) 1996-2009 by the original authors of JHotDraw
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

import javax.swing.*;
import org.jhotdraw.draw.*;

/**
 * Example showing how to layout two editable text figures and a line figure
 * within a graphical composite figure.
 *
 * @author Werner Randelshofer
 * @version $Id: LayouterSample.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class LayouterSample {
    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                
                // Create a graphical composite figure.
                GraphicalCompositeFigure composite = new GraphicalCompositeFigure();

                // Add child figures to the composite figure
                composite.add(new TextFigure("Above the line"));
                composite.add(new LineFigure());
                composite.add(new TextFigure("Below the line"));

                // Set a layouter and perform the layout
                composite.setLayouter(new VerticalLayouter());
                composite.layout();
                
                // Add the composite figure to a drawing
                Drawing drawing = new DefaultDrawing();
                drawing.add(composite);
                
                // Create a frame with a drawing view and a drawing editor
                JFrame f = new JFrame("My Drawing");
                f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
                f.setSize(400,300);
                DrawingView view = new DefaultDrawingView();
                view.setDrawing(drawing);
                f.getContentPane().add(view.getComponent());
                DrawingEditor editor = new DefaultDrawingEditor();
                editor.add(view);
                editor.setTool(new DelegationSelectionTool());
                f.setVisible(true);
            }
        });
    }
}
