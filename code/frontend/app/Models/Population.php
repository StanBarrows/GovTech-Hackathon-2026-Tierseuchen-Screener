<?php

namespace App\Models;

use Database\Factories\PopulationFactory;
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

#[Fillable(['name'])]
class Population extends Model
{
    /** @use HasFactory<PopulationFactory> */
    use HasFactory;
}
