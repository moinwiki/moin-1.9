/*
 * @(#)TeddyApplicationModel.java
 *
 * Copyright (c) 2007-2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.samples.teddy;

import javax.swing.*;
import org.jhotdraw.app.*;
import java.util.*;
import org.jhotdraw.app.action.*;
import org.jhotdraw.samples.teddy.action.*;
import org.jhotdraw.util.*;

/**
 * TeddyApplicationModel.
 *
 * @author Werner Randelshofer
 * @version $Id: TeddyApplicationModel.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class TeddyApplicationModel extends DefaultApplicationModel {
    
    /** Creates a new instance. */
    public TeddyApplicationModel() {
    }
    
    @Override public void initApplication(Application a) {
        putAction(org.jhotdraw.samples.teddy.action.FindAction.ID, new org.jhotdraw.samples.teddy.action.FindAction(a));
        putAction(ToggleLineWrapAction.ID, new ToggleLineWrapAction(a));
        putAction(ToggleStatusBarAction.ID, new ToggleStatusBarAction(a));
        putAction(ToggleLineNumbersAction.ID, new ToggleLineNumbersAction(a));
        putAction(PrintAction.ID, null);
    }
    
    @Override public void initView(Application a, View p) {
    }
    
    @Override public List<JMenu> createMenus(Application a, View p) {
        LinkedList<JMenu> mb = new LinkedList<JMenu>();
        
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.teddy.Labels");
        
        JMenu m;
        JCheckBoxMenuItem cbmi;
        
        mb.add(createEditMenu(a, p));
        
        m = new JMenu();
        labels.configureMenu(m, "view");
        cbmi = new JCheckBoxMenuItem(getAction(ToggleLineWrapAction.ID));
        Actions.configureJCheckBoxMenuItem(cbmi, getAction(ToggleLineWrapAction.ID));
        m.add(cbmi);
        cbmi = new JCheckBoxMenuItem(getAction(ToggleLineNumbersAction.ID));
        Actions.configureJCheckBoxMenuItem(cbmi, getAction(ToggleLineNumbersAction.ID));
        m.add(cbmi);
        cbmi = new JCheckBoxMenuItem(getAction(ToggleStatusBarAction.ID));
        Actions.configureJCheckBoxMenuItem(cbmi, getAction(ToggleStatusBarAction.ID));
        m.add(cbmi);
        mb.add(m);
        
        return mb;
    }
    
    /**
     * Creates toolbars for the application.
     * This class returns an empty list - we don't want toolbars in a text editor.
     */
    public List<JToolBar> createToolBars(Application app, View p) {
        return Collections.emptyList();
    }
}
