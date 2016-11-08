using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

namespace Core.Domain.Enums
{
    /// <summary>
    /// Enumeration class, from:
    /// https://lostechies.com/jimmybogard/2008/08/12/enumeration-classes/
    /// Enables the encapsulation of logic to the relevant classes and removes the need for switch statements when using enums.
    /// </summary>
    public abstract class Enumeration : IComparable
    {
        private int _value;
        private string _displayName;

        protected Enumeration()
        {
        }

        protected Enumeration(int value, string displayName)
        {
            _value = value;
            _displayName = displayName;
        }

        public int Value
        {
            get { return _value; }

            // Entity Framework will only retrieve and set the display name.
            // Use this setter to find the corresponding value as defined in the static fields.
            protected set
            {
                _value = value;

                // Get the static fields on the inheriting type.
                foreach (var field in GetType().GetFields(BindingFlags.Public | BindingFlags.Static))
                {
                    // If the static field is an Enumeration type.
                    var enumeration = field.GetValue(this) as Enumeration;
                    if (enumeration == null)
                    {
                        continue;
                    }

                    // Set the value of this instance to the value of the corresponding static type.
                    if (enumeration.Value == value)
                    {
                        _value = enumeration.Value;
                        break;
                    }
                }
            }
        }

        public string DisplayName
        {
            get { return _displayName; }
        }

        public override string ToString()
        {
            return DisplayName;
        }

        public static IEnumerable<T> GetAll<T>() where T : Enumeration, new()
        {
            var type = typeof(T);
            var fields = type.GetFields(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly);

            foreach (var info in fields)
            {
                var instance = new T();
                var locatedValue = info.GetValue(instance) as T;

                if (locatedValue != null)
                {
                    yield return locatedValue;
                }
            }
        }

        public override bool Equals(object obj)
        {
            var otherValue = obj as Enumeration;

            if (otherValue == null)
            {
                return false;
            }

            var typeMatches = GetType().Equals(obj.GetType());
            var valueMatches = _value.Equals(otherValue.Value);

            return typeMatches && valueMatches;
        }

        public override int GetHashCode()
        {
            return _value.GetHashCode();
        }

        public static int AbsoluteDifference(Enumeration firstValue, Enumeration secondValue)
        {
            var absoluteDifference = Math.Abs(firstValue.Value - secondValue.Value);
            return absoluteDifference;
        }

        public static T FromValue<T>(int value) where T : Enumeration, new()
        {
            var matchingItem = parse<T, int>(value, "value", item => item.Value == value);
            return matchingItem;
        }

        public static T FromDisplayName<T>(string displayName) where T : Enumeration, new()
        {
            var matchingItem = parse<T, string>(displayName, "display name", item => item.DisplayName == displayName);
            return matchingItem;
        }

        private static T parse<T, K>(K value, string description, Func<T, bool> predicate) where T : Enumeration, new()
        {
            var matchingItem = GetAll<T>().FirstOrDefault(predicate);

            if (matchingItem == null)
            {
                var message = string.Format("'{0}' is not a valid {1} in {2}", value, description, typeof(T));
                throw new ApplicationException(message);
            }

            return matchingItem;
        }

        public int CompareTo(object other)
        {
            return Value.CompareTo(((Enumeration)other).Value);
        }
    }
}
