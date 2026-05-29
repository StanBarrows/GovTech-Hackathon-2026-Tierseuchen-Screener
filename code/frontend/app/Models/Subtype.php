<?php

namespace App\Models;

use Database\Factories\SubtypeFactory;
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

#[Fillable(['name'])]
class Subtype extends Model
{
    /** @use HasFactory<SubtypeFactory> */
    use HasFactory;
}
