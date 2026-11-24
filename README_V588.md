# V588: preserve source function map identity during BAT scope planning

V586 original-free regression caught mutation of a shared parsed function-map object. Copy the map before inserting exact authenticated mapper roots; additionally require repeated deterministic planning and unchanged source map. V586's owner job was skipped because the independent test failed. V588 retriggers that gate. No native BAT coverage success yet.
