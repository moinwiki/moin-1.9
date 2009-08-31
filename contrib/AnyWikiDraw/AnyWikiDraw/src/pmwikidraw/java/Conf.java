import java.util.Stack;
import java.util.Hashtable;
import java.util.Enumeration;

import java.lang.reflect.Field;

import qdxml.DocHandler;
import qdxml.QDParser;

import java.io.FileReader;

/** An example of something you could do with
    the quick and dirty XML parser.  Populate
    a configuation structure by mapping xml
    elements to java objects. */
public class Conf implements DocHandler {
  // Classes for storing a star-ship's device configuration
  // follow.  Nothing too deep here....
  static class MissingSystem {}
  static class Engine {
    String spaceTimeSetting, spaceFoldRate;
  }
  static class Propulsion {
    Engine portWarpDrive = new Engine();
    Engine starboardWarpDrive = new Engine();
  }
  static class DefenseMechanism {
    String setting, frequency;
  }
  static class Defense {
    DefenseMechanism forceField = new DefenseMechanism();
    DefenseMechanism ecm = new DefenseMechanism();
  }
  static class Weapon {
    String power, setting;
  }
  static class CombatComputer {
    String subSystem, state;
  }
  static class Weapons {
    Weapon mainEnergyBeam = new Weapon();
    Weapon secondaryEnergyBeam = new Weapon();
    Weapon energyTorpedo = new Weapon();
    CombatComputer combatComputer = new CombatComputer();
  }
  static class AtmosphereSetting {
    String race, scent, level;
  }
  static class AtmosphereControl {
    AtmosphereSetting engineering = new AtmosphereSetting();
    AtmosphereSetting bridge = new AtmosphereSetting();
    AtmosphereSetting hydroponics = new AtmosphereSetting();
  }
  static class LifeSupport {
    AtmosphereControl atmosphere = new AtmosphereControl();
  }
  static class ShipConfig {
    Weapons weapons = new Weapons();
    Propulsion propulsion = new Propulsion();
    Defense defense = new Defense();
    LifeSupport lifeSupport = new LifeSupport();
  }
  // Everything above this line is just the classes
  // needed to describe a star-ship configuration.

  // The stack is used to get back to where we were
  // when we hit an endElement()
  Stack stack;

  // the object we are currently processing
  Object model = new ShipConfig();

  // we aren't really doing anything with this in this
  // example.
  public void text(String s) {}

  // Use reflection to set things.
  // <weapons> indicates that we want to start
  //           setting fields inside the field
  //           on the current object.
  // <weapon setting="foo"> means the same thing,
  //           except we also want to set the field
  //           named "setting" to the value "foo".
  // Reflection was used to accomplish this because
  // it made this example easy to write.
  public void startElement(String name,Hashtable h) {
    // The current object that we are processing is called "model"
    // The first thing we want to do is set model to the value of
    // the field in name.

    // diagnostic output
    System.out.println("  Configuring: "+name);
    if(stack.empty()) {
      stack.push(model);
    } else {
      stack.push(model);
      try {
        Field field = model.getClass().getDeclaredField(jname(name));
        model = field.get(model);
      } catch(Exception ex) {
	// You tried to set something that didn't exist
        System.out.println("Error:  missing field on "+
	  model.getClass().getName()+": "+name);
	model = new MissingSystem();
	return;
      }
    }

    // Set string fields on the current object.
    Enumeration e = h.keys();
    while(e.hasMoreElements()) {
      String key=null, val=null;
      try {
        key = (String)e.nextElement();
	val = (String)h.get(key);
	key = jname(key);
	System.out.println("    setting: "+key+" => "+val);
	Field field = model.getClass().getDeclaredField(key);

	// assume everything's a String
	field.set(model,val.toString());

      } catch(Exception ex) {
        System.out.println("Error:  missing field on "+
	  model.getClass().getName()+": "+key);
      }
    }
  }
  // return to the previous object.
  public void endElement(String name) {
    model = stack.pop();
  }
  public void startDocument() {
    stack = new Stack();
  }
  public void endDocument() {
    stack = null;
  }

  /** Convert an xml-style name to a java-style name.
      Example: primary-weapon becomes primaryWeapon. */
  public String jname(String s) {
    boolean ucase = false;
    StringBuffer sb = new StringBuffer();
    for(int i=0;i<s.length();i++) {
      char c = s.charAt(i);
      if(c == '-') {
        ucase = true;
      } else if(ucase) {
        sb.append(Character.toUpperCase(c));
	ucase = false;
      } else {
        sb.append(Character.toLowerCase(c));
      }
    }
    return sb.toString();
  }

  public static void main(String[] args) throws Exception {
    Conf c = new Conf();

    // we could reset this configuration data at
    // any time by re-reading config.xml.  Alternatively,
    // we could load another config file that selectively
    // modifies pieces of the whole configuration.
    QDParser.parse(c,new FileReader("config.xml"));
  }
}
