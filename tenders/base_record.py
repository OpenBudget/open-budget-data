import os
import json
import types
import sys

all_records = {}
indexes = {}

def iter_json_records( filename ):
    for line in open( filename, 'r' ).xreadlines():
        data = json.loads(line)
        yield data

def connected_to_db( f ):
    def dec( self, *p, **d ):

        if isinstance(self, types.ClassType):
            cls_name = self.__name__
        else:
            cls_name = self.__class__.__name__

        if cls_name not in all_records:
            self.load_records()
        return f( self, *p, **d )
    return dec

class base_record:
    def __init__( self, data ):
        self.data = data
        self.calculated_data = {}
        self._getitem_entered = []

    def __str__( self ):
        return '%s( %s )' % (self.__class__.__name__, repr(self.data))

    def __repr__( self ):
        return str(self)
            
    def __getitem__( self, k ):
        if k in self.data:
            return self.data.__getitem__(k)
        else:
            if k not in self._getitem_entered:
                if k not in self.calculated_data:
                    self._getitem_entered.append( k )
                    self.calculate_field( k )
                    self._getitem_entered.remove( k )
            return self.calculated_data.__getitem__(k)

    def __setitem__( self, k, v ):
        if k in self.data:
            return self.data.__setitem__(k, v)
        else:
            return self.calculated_data.__setitem__(k, v)

    def set_data_field( self, k, v ):
        self.data[k] = v

    def __iter__( self ):
        for y in self.data.__iter__():
            yield y
        for y in self.calculated_data.__iter__():
            yield y

    def __len__( self ):
        return self.data.__len__() + self.calculated_data.__len__()

    def __getstate__( self ):
        return self.data

    def __setstate__( self, s ):
        self.data = s
        self.calculated_data = {}

    def keys( self ):
        return self.data.keys()

    def add_index( self, index_name, index_value ):
        index_value = self.normalize_index( index_value )

        if index_value in indexes[self.__class__.__name__][index_name]:
            print 'record %s=%s already indexed' % (index_name, index_value)
            raise AssertionError( 'record %s=%s already indexed' % (index_name, index_value) )

        indexes[self.__class__.__name__][index_name][index_value] = self

    @classmethod
    @connected_to_db
    def has_record( cls, **d ):
        if len(d) != 1:
            raise SyntaxError( 'exactly one named argument expected' )

        k = d.keys()[0]
        v = cls.normalize_index( d[k] )

        if k not in indexes[cls.__name__]:
            raise KeyError( 'no such index %s' % k )

        return v in indexes[cls.__name__][k]

    @classmethod
    @connected_to_db
    def records_count( cls ):
        return len(all_records[cls.__name__])

        
    @classmethod
    def normalize_index( cls, data ):
        if type(data) in [str, unicode]:
            data = data.strip()
            if len(data) == 0:
                data = None

        return data

    @classmethod
    @connected_to_db
    def get_record( cls, **d ):
        if len(d) != 1:
            raise SyntaxError( 'exactly one named argument expected' )

        k = d.keys()[0]
        v = cls.normalize_index( d[k] )

        if k not in indexes[cls.__name__]:
            raise KeyError( 'no such index %s' % str(k) )

        if v not in indexes[cls.__name__][k]:
            raise IndexError( '%s=%s' % (str(k), str(v)) )
            
        return indexes[cls.__name__][k][v]

    @connected_to_db
    def add_to_db( self ):
        if self.exists():
            raise AssertionError( 'record already exists' )

        all_records[self.__class__.__name__].append( self )
        self.index_record()

    @classmethod
    def load_records( cls ):

        #print 'load_records', cls

        if cls.__name__ in all_records:
            raise AssertionError( 'db %s already loaded' % cls.db_filename )

        all_records[cls.__name__] = []
        indexes[cls.__name__] = {x:{} for x in cls.index_names}

        if not os.path.exists( cls.db_filename ):
            return

        print "loading %s db %s ..." % (cls.__name__, cls.db_filename),
        sys.stdout.flush()
        
        for record in iter_json_records( cls.db_filename ):
            
            record = cls(record)

            if record.exists():
                if record.diff():
                    raise AssertionError( 'collisions in data' )
                continue
        
            record.add_to_db()
        print "done"


    @classmethod
    @connected_to_db
    def write_records( cls ):

        print "writing %s..." % cls.db_filename, 
        sys.stdout.flush()

        f = open( cls.db_filename, 'w' )
    
        for record in cls.iter_records():
            f.write( json.dumps(record.data) + '\n' )

        f.close()

        print "done"


    def check_filter( self, match_all, filter_field, filter_value ):

        # TODO: remove the following:
        if filter_field not in self:
            return False
        

        if type(filter_value) is list:
            if type(self[filter_field]) is list:
                
                if match_all:
                
                    # all of the list elems in the filter must exist in the record
                    return set(filter_value).issubset(self[filter_field])
                    
                else:

                    # the list elems in the filter must intersect with the record
                    return len(set(filter_value).intersection(self[filter_field])) > 0
                
            else:

                # match a value within a list of values
                return self[filter_field] in filter_value
                
        else:

            # exact match
            return self[filter_field] == filter_value


    def filter_record( self, match_all, **filters):
        for filter_field, filter_value in filters.iteritems():
            if self.check_filter( match_all, filter_field, filter_value ):
                if not match_all:
                    return True
            else:
                if match_all:
                    return False
        return True
        
    @classmethod
    @connected_to_db
    def iter_records( cls, match_all=True, **filters ):
        for record in all_records[cls.__name__]:
            if len(filters):
                if record.filter_record( match_all, **filters ):
                    yield record
            else:
                yield record
